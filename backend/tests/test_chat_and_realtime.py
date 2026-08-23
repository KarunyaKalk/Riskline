import pytest
from fastapi import status

from app.core.events import event_broadcaster
from app.services.risk_engine import run_risk_analysis_pipeline


def test_chat_streaming_and_audience_modes(client):
    res = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "Chat Org", "email": "engineer@chat.com", "password": "Password123!"},
    )
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Send chat message stream (technical mode)
    tech_resp = client.post(
        "/api/v1/chat/stream",
        json={"session_id": "main", "message": "What is the database schema migration impact?", "audience": "technical"},
        headers=headers,
    )
    assert tech_resp.status_code == status.HTTP_200_OK
    assert "text/event-stream" in tech_resp.headers["content-type"]
    assert "data:" in tech_resp.text

    # 2. Send chat message stream (business mode)
    biz_resp = client.post(
        "/api/v1/chat/stream",
        json={"session_id": "main", "message": "Explain the database change for stakeholders", "audience": "business"},
        headers=headers,
    )
    assert biz_resp.status_code == status.HTTP_200_OK
    assert "data:" in biz_resp.text

    # 3. Retrieve chat history
    history = client.get("/api/v1/chat/history?session_id=main", headers=headers).json()
    assert history["total"] >= 4  # 2 user messages + 2 assistant messages
    assert history["items"][0]["role"] == "user"
    assert history["items"][1]["role"] == "assistant"


def test_chat_tenant_and_session_isolation(client):
    # Org A
    res_a = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "Chat Tenant Org A", "email": "user@chata.com", "password": "Password123!"},
    )
    headers_a = {"Authorization": f"Bearer {res_a.json()['access_token']}"}

    client.post(
        "/api/v1/chat/stream",
        json={"session_id": "secret-session", "message": "Confidential internal architecture key", "audience": "technical"},
        headers=headers_a,
    )

    # Org B
    res_b = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "Chat Tenant Org B", "email": "user@chatb.com", "password": "Password123!"},
    )
    headers_b = {"Authorization": f"Bearer {res_b.json()['access_token']}"}

    # Org B queries chat history for secret-session
    history_b = client.get("/api/v1/chat/history?session_id=secret-session", headers=headers_b).json()
    assert history_b["total"] == 0


@pytest.mark.asyncio
async def test_realtime_event_broadcasting_isolation(db_session):
    import uuid

    org_a = uuid.uuid4()
    org_b = uuid.uuid4()

    # Create sub-generators
    gen_a = event_broadcaster.subscribe(org_a)
    gen_b = event_broadcaster.subscribe(org_b)

    # Initialize connections
    init_a = await gen_a.__anext__()
    init_b = await gen_b.__anext__()

    assert str(org_a) in init_a
    assert str(org_b) in init_b

    # Publish event strictly to Org A
    await event_broadcaster.publish_async(org_a, "CHANGE_CREATED", {"title": "Org A Deployment"})

    event_a = await gen_a.__anext__()
    assert "CHANGE_CREATED" in event_a
    assert "Org A Deployment" in event_a


def test_notification_triggering_and_preferences(client, db_session):
    from app.models.user import User

    res = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "Notif Org", "email": "admin@notif.com", "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {res.json()['access_token']}"}
    user = db_session.query(User).filter(User.email == "admin@notif.com").first()

    # 1. Create high risk change
    c = client.post(
        "/api/v1/changes",
        json={
            "title": "Drop Users Table Column",
            "description": "ALTER TABLE users DROP COLUMN password_hash; High-risk schema migration.",
            "status": "pending",
        },
        headers=headers,
    ).json()

    # 2. Trigger risk analysis (evaluates at high/critical risk)
    run_risk_analysis_pipeline(db_session, user.org_id, c["id"])

    # 3. Check notifications endpoint
    notif_res = client.get("/api/v1/notifications", headers=headers).json()
    assert notif_res["total"] > 0
    assert notif_res["unread_count"] > 0

    notif_id = notif_res["items"][0]["id"]

    # 4. Mark notification as read
    read_res = client.put(f"/api/v1/notifications/{notif_id}/read", headers=headers).json()
    assert read_res["is_read"] == True

    # 5. Check preferences & update
    pref_res = client.get("/api/v1/notifications/preferences", headers=headers).json()
    assert pref_res["inapp_enabled"] == True

    upd_pref = client.put(
        "/api/v1/notifications/preferences",
        json={"email_enabled": False, "slack_enabled": False},
        headers=headers,
    ).json()
    assert upd_pref["email_enabled"] == False
    assert upd_pref["slack_enabled"] == False
