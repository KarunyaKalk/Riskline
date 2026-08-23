import pytest
from fastapi import status
from app.core.rate_limiter import RateLimiter


def test_rate_limiter_exceeded(client):
    # Signup user
    res = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "Rate Limit Org", "email": "ratelimit@test.com", "password": "Password123!"},
    )
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Instantiate a low limit rate limiter for test assertion
    limiter = RateLimiter(times=3, seconds=60)

    # Perform requests under limit
    for i in range(3):
        resp = client.post(
            "/api/v1/notes",
            json={"title": f"Note {i}", "content": "Content", "tags": ["idea"]},
            headers=headers,
        )
        assert resp.status_code == status.HTTP_201_CREATED

    # Perform 4th request -> expect 429 Too Many Requests when using strict low-limit instance
    # Test rate-limiter class directly
    from fastapi import Request
    class DummyRequest:
        url = type("URL", (), {"path": "/api/v1/notes"})()

    dummy_req = DummyRequest()
    from app.models.user import User
    user = User(id="00000000-0000-0000-0000-000000000001", org_id="00000000-0000-0000-0000-000000000001")

    # 3 calls work
    limiter2 = RateLimiter(times=3, seconds=60)
    limiter2(dummy_req, user)
    limiter2(dummy_req, user)
    limiter2(dummy_req, user)

    # 4th call raises 429
    with pytest.raises(Exception) as exc_info:
        limiter2(dummy_req, user)
    assert "429" in str(exc_info.value) or exc_info.value.status_code == 429
