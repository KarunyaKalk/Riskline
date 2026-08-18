import pytest
from fastapi import status
from app.models.user import User, UserRole
from app.models.audit_log import AuditLog
from app.models.team_member import TeamMember


def test_signup_creates_org_and_admin_user(client, db_session):
    payload = {
        "org_name": "Acme Engineering",
        "email": "admin@acme.com",
        "password": "SecurePassword123!",
    }
    response = client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()

    # Check user & organization output
    assert data["user"]["email"] == "admin@acme.com"
    assert data["user"]["role"] == "admin"
    assert data["user"]["status"] == "active"
    assert data["organization"]["name"] == "Acme Engineering"
    assert "slug" in data["organization"]
    assert data["organization"]["plan"] == "free"
    assert "access_token" in data
    assert "refresh_token" in data

    # Verify HttpOnly cookies set in response
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies

    # Verify TeamMember roster entry created
    tm = db_session.query(TeamMember).filter(TeamMember.email == "admin@acme.com").first()
    assert tm is not None
    assert tm.role == "Organization Admin"

    # Verify AuditLog created
    log = db_session.query(AuditLog).filter(AuditLog.action == "USER_SIGNUP").first()
    assert log is not None
    assert log.target_type == "user"


def test_login_success_and_failure(client, db_session):
    # Signup first
    signup_payload = {
        "org_name": "Stark Industries",
        "email": "tony@stark.com",
        "password": "JarvisPassword123!",
    }
    client.post("/api/v1/auth/signup", json=signup_payload)

    # 1. Login with correct credentials
    login_payload = {
        "email": "tony@stark.com",
        "password": "JarvisPassword123!",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["user"]["email"] == "tony@stark.com"
    assert "access_token" in data

    # Verify AuditLog created for login
    login_log = db_session.query(AuditLog).filter(AuditLog.action == "USER_LOGIN").first()
    assert login_log is not None

    # 2. Login with incorrect password
    bad_login = {
        "email": "tony@stark.com",
        "password": "WrongPassword!",
    }
    bad_resp = client.post("/api/v1/auth/login", json=bad_login)
    assert bad_resp.status_code == status.HTTP_401_UNAUTHORIZED

    # 3. Login with nonexistent email
    nonexistent_resp = client.post("/api/v1/auth/login", json={"email": "nobody@stark.com", "password": "pass"})
    assert nonexistent_resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_unauthenticated_request_rejected(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_rbac_admin_only_permission(client, db_session):
    # 1. Signup Admin User
    res = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "Shield", "email": "fury@shield.com", "password": "ShieldPassword123!"},
    )
    admin_token = res.json()["access_token"]
    admin_user = db_session.query(User).filter(User.email == "fury@shield.com").first()

    # Admin access should succeed
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    admin_resp = client.get("/api/v1/auth/admin-only", headers=admin_headers)
    assert admin_resp.status_code == status.HTTP_200_OK

    # 2. Demote user role to ENGINEER to test RBAC rejection
    admin_user.role = UserRole.ENGINEER
    db_session.commit()

    # Engineer access to admin-only endpoint should be forbidden (403)
    eng_resp = client.get("/api/v1/auth/admin-only", headers=admin_headers)
    assert eng_resp.status_code == status.HTTP_403_FORBIDDEN


def test_cross_org_isolation(client):
    """
    CRITICAL MULTI-TENANCY TEST:
    Verifies that User from Org A cannot read data belonging to Org B.
    """
    # 1. Signup Org A (Acme Corp) with User A
    res_a = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "Acme Corp", "email": "alice@acme.com", "password": "AlicePassword123!"},
    )
    assert res_a.status_code == 201
    token_a = res_a.json()["access_token"]

    # 2. Signup Org B (Beta Inc) with User B
    res_b = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "Beta Inc", "email": "bob@beta.com", "password": "BobPassword123!"},
    )
    assert res_b.status_code == 201
    token_b = res_b.json()["access_token"]

    # 3. User A requests org-users list
    headers_a = {"Authorization": f"Bearer {token_a}"}
    users_a_resp = client.get("/api/v1/auth/org-users", headers=headers_a)
    assert users_a_resp.status_code == 200
    users_a = users_a_resp.json()

    # User A's list should contain ONLY Alice (1 user) and NOT Bob
    assert len(users_a) == 1
    assert users_a[0]["email"] == "alice@acme.com"

    # 4. User B requests org-users list
    headers_b = {"Authorization": f"Bearer {token_b}"}
    users_b_resp = client.get("/api/v1/auth/org-users", headers=headers_b)
    assert users_b_resp.status_code == 200
    users_b = users_b_resp.json()

    # User B's list should contain ONLY Bob (1 user) and NOT Alice
    assert len(users_b) == 1
    assert users_b[0]["email"] == "bob@beta.com"

    # 5. Verify User A calling /me receives Alice's Org A details and not Org B
    me_a = client.get("/api/v1/auth/me", headers=headers_a).json()
    assert me_a["organization"]["name"] == "Acme Corp"
    assert me_a["user"]["email"] == "alice@acme.com"
