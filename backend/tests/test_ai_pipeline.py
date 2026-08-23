import io
import pytest
from fastapi import status
from pypdf import PdfWriter

from app.services.embedding_service import index_change_text, search_similar_chunks
from app.services.llm_client import llm_client
from app.services.risk_engine import run_risk_analysis_pipeline


def test_pdf_upload_and_risk_analysis_pipeline(client):
    # 1. Signup User
    res = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "AI Pipeline Org", "email": "engineer@aipipeline.com", "password": "Password123!"},
    )
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Upload text change record
    change_res = client.post(
        "/api/v1/changes",
        json={
            "title": "Upgrade Postgres Database Schema",
            "description": "Executing alter table migration to drop legacy column user_password and update indexed FKs.",
            "status": "pending",
        },
        headers=headers,
    )
    assert change_res.status_code == status.HTTP_201_CREATED
    change_id = change_res.json()["id"]

    # 3. Trigger risk analysis
    analysis_res = client.post(f"/api/v1/changes/{change_id}/analyze", headers=headers)
    assert analysis_res.status_code == status.HTTP_200_OK
    analysis = analysis_res.json()
    assert analysis["risk_level"] in ["low", "medium", "high", "critical"]
    assert "technical_summary" in analysis
    assert "business_summary" in analysis
    assert isinstance(analysis["recommendations"], list)
    assert len(analysis["recommendations"]) > 0

    # 4. Fetch risk analysis output via GET
    get_analysis = client.get(f"/api/v1/changes/{change_id}/risk-analysis", headers=headers)
    assert get_analysis.status_code == status.HTTP_200_OK
    assert get_analysis.json()["id"] == analysis["id"]


def test_invalid_pdf_rejection(client):
    res = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "PDF Test Org", "email": "pdf@test.com", "password": "Password123!"},
    )
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Upload fake non-PDF file
    invalid_file = ("test.txt", b"This is plain text, not a PDF", "application/pdf")
    resp = client.post("/api/v1/changes/upload-pdf", files={"file": invalid_file}, headers=headers)
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "not a valid PDF document" in resp.json()["detail"]


def test_rag_vector_cross_tenant_isolation(client, db_session):
    from app.models.user import User

    # 1. Org A
    res_a = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "RAG Org A", "email": "user@rag-a.com", "password": "Password123!"},
    )
    token_a = res_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    user_a = db_session.query(User).filter(User.email == "user@rag-a.com").first()

    # Org A creates and indexes a confidential change
    change_a = client.post(
        "/api/v1/changes",
        json={
            "title": "Confidential Security Key Rotation",
            "description": "Rotating AES-256 cryptographic master encryption keys and updating JWT signature secrets.",
            "status": "pending",
        },
        headers=headers_a,
    ).json()

    # Trigger analysis for Org A change to build RAG vector embeddings
    client.post(f"/api/v1/changes/{change_a['id']}/analyze", headers=headers_a)

    # 2. Org B
    res_b = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "RAG Org B", "email": "user@rag-b.com", "password": "Password123!"},
    )
    user_b = db_session.query(User).filter(User.email == "user@rag-b.com").first()

    # Org B queries RAG semantic search for Org A's exact confidential terms
    query_text = "Rotating AES-256 cryptographic master encryption keys"
    results_org_b = search_similar_chunks(db_session, user_b.org_id, query_text, top_k=5)

    # CRITICAL SECURITY CHECK: Org B vector search MUST return 0 results from Org A
    assert len(results_org_b) == 0

    # Org A queries RAG semantic search for same terms -> MUST find Org A's chunks
    results_org_a = search_similar_chunks(db_session, user_a.org_id, query_text, top_k=5)
    assert len(results_org_a) > 0
    assert "AES-256" in results_org_a[0][0].chunk_text


def test_realistic_deployment_scenarios(client):
    # Test realistic risk assessments across 5 deployment types
    scenarios = [
        {
            "title": "Postgres Database Schema Drop Column",
            "text": "ALTER TABLE users DROP COLUMN password_hash CASCADE; Executing database schema migration.",
            "expected_min_risk": 7.0,
        },
        {
            "title": "Rotate JWT Auth Token Signing Secrets",
            "text": "Updating authentication middleware JWT signing secret and Argon2 hashing parameters.",
            "expected_min_risk": 7.0,
        },
        {
            "title": "Kubernetes Ingress Controller Upgrade",
            "text": "Upgrading Nginx ingress controller in k8s cluster from v1.8 to v1.9 and updating SSL certificates.",
            "expected_min_risk": 4.0,
        },
        {
            "title": "Flush and Restart Redis Cache Cluster",
            "text": "Restarting Redis cluster instances and purging transient cache entries.",
            "expected_min_risk": 4.0,
        },
        {
            "title": "Fix Typo in Frontend CSS Footer",
            "text": "Updating copyright year and fixing minor CSS padding in frontend footer component.",
            "expected_min_risk": 0.0,
        },
    ]

    res = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "Scenario Test Org", "email": "scenarios@test.com", "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {res.json()['access_token']}"}

    for sc in scenarios:
        c = client.post(
            "/api/v1/changes",
            json={"title": sc["title"], "description": sc["text"], "status": "pending"},
            headers=headers,
        ).json()

        analysis_res = client.post(f"/api/v1/changes/{c['id']}/analyze", headers=headers)
        assert analysis_res.status_code == status.HTTP_200_OK
        analysis = analysis_res.json()
        assert analysis["risk_score"] >= sc["expected_min_risk"]
