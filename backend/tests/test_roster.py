import pytest
from fastapi import status


def test_roster_crud_and_permissions(client):
    # 1. Signup Admin user for Org A
    signup_res = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "Org A Roster", "email": "admin@orga.com", "password": "Password123!"},
    )
    assert signup_res.status_code == status.HTTP_201_CREATED
    admin_token = signup_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Create team member (Admin allowed)
    create_res = client.post(
        "/api/v1/team-members",
        json={
            "name": "Sarah Connor",
            "email": "sarah@orga.com",
            "role": "Lead SRE",
            "status": "active",
        },
        headers=headers,
    )
    assert create_res.status_code == status.HTTP_201_CREATED
    member_data = create_res.json()
    member_id = member_data["id"]
    assert member_data["name"] == "Sarah Connor"
    assert member_data["role"] == "Lead SRE"

    # 3. List team members
    list_res = client.get("/api/v1/team-members", headers=headers)
    assert list_res.status_code == status.HTTP_200_OK
    list_data = list_res.json()
    assert list_data["total"] >= 2  # Initial admin + Sarah
    assert any(m["email"] == "sarah@orga.com" for m in list_data["items"])

    # 4. Get team member by ID
    get_res = client.get(f"/api/v1/team-members/{member_id}", headers=headers)
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["name"] == "Sarah Connor"

    # 5. Update team member (Admin allowed)
    update_res = client.put(
        f"/api/v1/team-members/{member_id}",
        json={"role": "Principal DevOps Architect"},
        headers=headers,
    )
    assert update_res.status_code == status.HTTP_200_OK
    assert update_res.json()["role"] == "Principal DevOps Architect"

    # 6. Delete team member (Admin allowed)
    del_res = client.delete(f"/api/v1/team-members/{member_id}", headers=headers)
    assert del_res.status_code == status.HTTP_204_NO_CONTENT

    # 7. Verify deletion
    get_after_del = client.get(f"/api/v1/team-members/{member_id}", headers=headers)
    assert get_after_del.status_code == status.HTTP_404_NOT_FOUND


def test_roster_viewer_permission_restriction(client, db_session):
    from app.models.user import User, UserRole

    # 1. Signup Admin user
    signup_res = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "Roster Perm Org", "email": "admin@perm.com", "password": "Password123!"},
    )
    token = signup_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Demote user to VIEWER
    user = db_session.query(User).filter(User.email == "admin@perm.com").first()
    user.role = UserRole.VIEWER
    db_session.commit()

    # 2. Viewer attempting to create team member should receive 403 Forbidden
    create_res = client.post(
        "/api/v1/team-members",
        json={"name": "Forbidden Member", "email": "bad@perm.com", "role": "Dev"},
        headers=headers,
    )
    assert create_res.status_code == status.HTTP_403_FORBIDDEN

    # 3. Viewer can list team members
    list_res = client.get("/api/v1/team-members", headers=headers)
    assert list_res.status_code == status.HTTP_200_OK


def test_roster_cross_tenant_isolation(client):
    # Signup Org A
    res_a = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "Org A Roster Iso", "email": "admin@orga-iso.com", "password": "Password123!"},
    )
    token_a = res_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Create team member in Org A
    member_a = client.post(
        "/api/v1/team-members",
        json={"name": "Alice A", "email": "alice@orga-iso.com", "role": "DevOps"},
        headers=headers_a,
    ).json()
    id_a = member_a["id"]

    # Signup Org B
    res_b = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "Org B Roster Iso", "email": "admin@orgb-iso.com", "password": "Password123!"},
    )
    token_b = res_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Org B user cannot get Org A's team member
    get_res = client.get(f"/api/v1/team-members/{id_a}", headers=headers_b)
    assert get_res.status_code == status.HTTP_404_NOT_FOUND

    # Org B user cannot update Org A's team member
    update_res = client.put(f"/api/v1/team-members/{id_a}", json={"role": "Hacker"}, headers=headers_b)
    assert update_res.status_code == status.HTTP_404_NOT_FOUND

    # Org B user cannot delete Org A's team member
    del_res = client.delete(f"/api/v1/team-members/{id_a}", headers=headers_b)
    assert del_res.status_code == status.HTTP_404_NOT_FOUND
