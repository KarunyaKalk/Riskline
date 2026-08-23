import pytest
from fastapi import status


def test_changes_crud_status_filtering_and_author_linking(client):
    # Signup user (Alice)
    res_a = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "Changes Org", "email": "alice@changes.com", "password": "Password123!"},
    )
    user_a = res_a.json()["user"]
    token_a = res_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 1. Create deployment changes
    c1 = client.post(
        "/api/v1/changes",
        json={
            "title": "Upgrade Redis Cluster to v7.2",
            "description": "Upgrading Redis cache cluster for low-latency session store",
            "status": "pending",
            "risk_score": 3.5,
        },
        headers=headers_a,
    ).json()

    c2 = client.post(
        "/api/v1/changes",
        json={
            "title": "Hotfix Auth JWT Token Expiration",
            "description": "Fix token expiration validation in FastAPI middleware",
            "status": "deployed",
            "risk_score": 1.2,
        },
        headers=headers_a,
    ).json()

    # Verify author_id is linked strictly to Alice's user.id
    assert c1["author_id"] == user_a["id"]
    assert c2["author_id"] == user_a["id"]

    # 2. List changes with status filter=deployed
    deployed_list = client.get("/api/v1/changes?status=deployed", headers=headers_a).json()
    assert deployed_list["total"] == 1
    assert deployed_list["items"][0]["title"] == "Hotfix Auth JWT Token Expiration"

    # 3. Filter by author_id
    author_list = client.get(f"/api/v1/changes?author_id={user_a['id']}", headers=headers_a).json()
    assert author_list["total"] == 2

    # 4. Get change details
    get_res = client.get(f"/api/v1/changes/{c1['id']}", headers=headers_a)
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["title"] == "Upgrade Redis Cluster to v7.2"

    # 5. Update change status
    update_res = client.put(
        f"/api/v1/changes/{c1['id']}",
        json={"status": "approved", "risk_score": 2.0},
        headers=headers_a,
    )
    assert update_res.status_code == status.HTTP_200_OK
    assert update_res.json()["status"] == "approved"

    # 6. Delete change
    del_res = client.delete(f"/api/v1/changes/{c1['id']}", headers=headers_a)
    assert del_res.status_code == status.HTTP_204_NO_CONTENT


def test_changes_cross_tenant_isolation(client):
    # Org A change
    res_a = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "Change Org A", "email": "admin@change-a.com", "password": "Password123!"},
    )
    headers_a = {"Authorization": f"Bearer {res_a.json()['access_token']}"}
    change_a = client.post(
        "/api/v1/changes",
        json={"title": "Org A Change", "description": "Secret Change", "status": "pending"},
        headers=headers_a,
    ).json()

    # Org B user
    res_b = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "Change Org B", "email": "admin@change-b.com", "password": "Password123!"},
    )
    headers_b = {"Authorization": f"Bearer {res_b.json()['access_token']}"}

    cid = change_a["id"]
    assert client.get(f"/api/v1/changes/{cid}", headers=headers_b).status_code == status.HTTP_404_NOT_FOUND
    assert client.put(f"/api/v1/changes/{cid}", json={"status": "approved"}, headers=headers_b).status_code == status.HTTP_404_NOT_FOUND
    assert client.delete(f"/api/v1/changes/{cid}", headers=headers_b).status_code == status.HTTP_404_NOT_FOUND
