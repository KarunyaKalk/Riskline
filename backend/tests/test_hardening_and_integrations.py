import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from app.models.organization import Organization
from app.models.user import User, UserRole
from app.models.password_reset import PasswordResetToken
from app.core.security import hash_password, verify_password


def test_power_bi_export_flow_and_tenant_isolation(client, db_session):
    # 1. Create Org A and Admin User
    org_a = Organization(name="Org Alpha", slug="org-alpha")
    db_session.add(org_a)
    db_session.flush()

    user_a = User(
        org_id=org_a.id,
        email="admin@alpha.com",
        hashed_password=hash_password("Password123!"),
        role=UserRole.ADMIN,
    )
    db_session.add(user_a)
    db_session.commit()

    # 2. Login as Admin Alpha and issue Power BI API Key
    login_resp = client.post("/api/v1/auth/login", json={"email": "admin@alpha.com", "password": "Password123!"})
    assert login_resp.status_code == 200
    access_token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    key_resp = client.post("/api/v1/export/api-keys", json={"name": "Power BI Desktop Key"}, headers=headers)
    assert key_resp.status_code == 201
    raw_key = key_resp.json()["api_key"]
    assert raw_key.startswith("rk_live_")

    # 3. Export Power BI data using X-API-Key header
    export_resp = client.get("/api/v1/export/power-bi", headers={"X-API-Key": raw_key})
    assert export_resp.status_code == 200
    export_data = export_resp.json()
    assert export_data["organization"] == "Org Alpha"
    assert export_data["org_id"] == str(org_a.id)
    assert "summary" in export_data
    assert "changes" in export_data

    # 4. Reject request with invalid API Key
    invalid_resp = client.get("/api/v1/export/power-bi", headers={"X-API-Key": "rk_live_invalid_key"})
    assert invalid_resp.status_code == 401


def test_password_reset_single_use_and_expiration(client, db_session):
    # 1. Create Org and User
    org = Organization(name="Reset Test Org", slug="reset-org")
    db_session.add(org)
    db_session.flush()

    user = User(
        org_id=org.id,
        email="reset_user@test.com",
        hashed_password=hash_password("OldPassword123!"),
        role=UserRole.ENGINEER,
    )
    db_session.add(user)
    db_session.commit()

    # 2. Request forgot password
    forgot_resp = client.post("/api/v1/auth/forgot-password", json={"email": "reset_user@test.com"})
    assert forgot_resp.status_code == 200
    reset_token = forgot_resp.json()["reset_token"]
    assert reset_token is not None

    # 3. Execute password reset
    reset_resp = client.post("/api/v1/auth/reset-password", json={"token": reset_token, "new_password": "NewSecretPassword123!"})
    assert reset_resp.status_code == 200
    assert reset_resp.json()["message"] == "Password successfully reset."

    # 4. Confirm user can now login with new password
    login_resp = client.post("/api/v1/auth/login", json={"email": "reset_user@test.com", "password": "NewSecretPassword123!"})
    assert login_resp.status_code == 200

    # 5. Reject attempt to reuse the same reset token (Single-Use Protection)
    reuse_resp = client.post("/api/v1/auth/reset-password", json={"token": reset_token, "new_password": "AnotherPassword123!"})
    assert reuse_resp.status_code == 400
    assert "Invalid, expired, or previously used" in reuse_resp.json()["detail"]


def test_malformed_pdf_upload_rejection(client, db_session):
    # Setup auth
    org = Organization(name="PDF Test Org", slug="pdf-org")
    db_session.add(org)
    db_session.flush()

    user = User(
        org_id=org.id,
        email="pdf_user@test.com",
        hashed_password=hash_password("Password123!"),
        role=UserRole.ENGINEER,
    )
    db_session.add(user)
    db_session.commit()

    login_resp = client.post("/api/v1/auth/login", json={"email": "pdf_user@test.com", "password": "Password123!"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Upload malformed PDF content (not starting with %PDF)
    malformed_pdf_bytes = b"This is invalid text masquerading as a PDF file"
    files = {"file": ("malformed.pdf", malformed_pdf_bytes, "application/pdf")}

    upload_resp = client.post("/api/v1/changes/upload-pdf", files=files, headers=headers)
    assert upload_resp.status_code == 400
    assert "valid pdf" in upload_resp.json()["detail"].lower()
