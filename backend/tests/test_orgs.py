import pytest
from fastapi import status


def test_invite_generation_and_acceptance_flow(client):
    # 1. Admin (Alice) signs up Org A
    res_a = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "Invite Test Org", "email": "alice@invitetest.com", "password": "Password123!"},
    )
    headers_a = {"Authorization": f"Bearer {res_a.json()['access_token']}"}

    # 2. Admin invites teammate Bob as ENGINEER
    invite_res = client.post(
        "/api/v1/orgs/invites",
        json={"email": "bob@invitetest.com", "role": "engineer"},
        headers=headers_a,
    )
    assert invite_res.status_code == status.HTTP_201_CREATED
    invite_data = invite_res.json()
    token = invite_data["token"]
    assert invite_data["email"] == "bob@invitetest.com"
    assert invite_data["status"] == "pending"

    # 3. Unauthenticated user inspects invite token details
    inspect_res = client.get(f"/api/v1/orgs/invites/{token}")
    assert inspect_res.status_code == status.HTTP_200_OK
    assert inspect_res.json()["email"] == "bob@invitetest.com"

    # 4. Bob accepts invite and sets password
    accept_res = client.post(
        "/api/v1/orgs/invites/accept",
        json={"token": token, "password": "BobSecurePassword123!", "name": "Bob Marley"},
    )
    assert accept_res.status_code == status.HTTP_201_CREATED
    bob_user = accept_res.json()
    assert bob_user["email"] == "bob@invitetest.com"
    assert bob_user["role"] == "engineer"

    # 5. Token cannot be reused
    reaccept = client.post(
        "/api/v1/orgs/invites/accept",
        json={"token": token, "password": "BobSecurePassword123!"},
    )
    assert reaccept.status_code == status.HTTP_400_BAD_REQUEST


def test_member_role_update_and_removal(client, db_session):
    from app.models.user import User, UserRole

    # 1. Signup Admin
    res_a = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "Member Mgmt Org", "email": "admin@membermgmt.com", "password": "Password123!"},
    )
    token_a = res_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Invite & accept member Bob
    inv_res = client.post(
        "/api/v1/orgs/invites",
        json={"email": "bob@membermgmt.com", "role": "engineer"},
        headers=headers_a,
    )
    token = inv_res.json()["token"]
    bob_res = client.post(
        "/api/v1/orgs/invites/accept",
        json={"token": token, "password": "BobPassword123!"},
    ).json()
    bob_id = bob_res["id"]

    # 3. Update Bob's role to BUSINESS_OPS (Admin allowed)
    role_res = client.put(
        f"/api/v1/orgs/members/{bob_id}/role",
        json={"role": "business_ops"},
        headers=headers_a,
    )
    assert role_res.status_code == status.HTTP_200_OK
    assert role_res.json()["role"] == "business_ops"

    # 4. Sole admin demoting self should be rejected (400)
    admin_id = res_a.json()["user"]["id"]
    demote_self = client.put(
        f"/api/v1/orgs/members/{admin_id}/role",
        json={"role": "engineer"},
        headers=headers_a,
    )
    assert demote_self.status_code == status.HTTP_400_BAD_REQUEST

    # 5. Sole admin removing self should be rejected (400)
    remove_self = client.delete(f"/api/v1/orgs/members/{admin_id}", headers=headers_a)
    assert remove_self.status_code == status.HTTP_400_BAD_REQUEST

    # 6. Admin removes Bob
    remove_bob = client.delete(f"/api/v1/orgs/members/{bob_id}", headers=headers_a)
    assert remove_bob.status_code == status.HTTP_204_NO_CONTENT

    # Verify Bob is removed
    members = client.get("/api/v1/orgs/members", headers=headers_a).json()
    assert not any(m["id"] == bob_id for m in members)


def test_orgs_cross_tenant_isolation(client):
    # Org A
    res_a = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "Org A Mgmt", "email": "admin@org-a.com", "password": "Password123!"},
    )
    token_a = res_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Org B
    res_b = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "Org B Mgmt", "email": "admin@org-b.com", "password": "Password123!"},
    )
    headers_b = {"Authorization": f"Bearer {res_b.json()['access_token']}"}
    user_b_id = res_b.json()["user"]["id"]

    # Org A admin attempting to change Org B member's role should fail (404)
    res = client.put(
        f"/api/v1/orgs/members/{user_b_id}/role",
        json={"role": "viewer"},
        headers=headers_a,
    )
    assert res.status_code == status.HTTP_404_NOT_FOUND

    # Org A admin attempting to remove Org B member should fail (404)
    del_res = client.delete(f"/api/v1/orgs/members/{user_b_id}", headers=headers_a)
    assert del_res.status_code == status.HTTP_404_NOT_FOUND
