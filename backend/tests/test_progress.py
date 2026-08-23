import pytest
from fastapi import status


def test_project_progress_crud_and_permissions(client, db_session):
    from app.models.user import User, UserRole

    # 1. Signup Admin (Alice)
    res_a = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "Progress Org", "email": "admin@prog.com", "password": "Password123!"},
    )
    headers_a = {"Authorization": f"Bearer {res_a.json()['access_token']}"}

    # 2. Create project progress item (Admin allowed)
    create_res = client.post(
        "/api/v1/project-progress",
        json={"title": "Q3 Kubernetes Cluster Migration", "status": "in_progress", "progress_pct": 45},
        headers=headers_a,
    )
    assert create_res.status_code == status.HTTP_201_CREATED
    item_id = create_res.json()["id"]

    # 3. Create Viewer User (Bob)
    res_b = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "Dummy B", "email": "viewer@prog.com", "password": "Password123!"},
    )
    user_b = db_session.query(User).filter(User.email == "viewer@prog.com").first()
    user_a = db_session.query(User).filter(User.email == "admin@prog.com").first()
    user_b.org_id = user_a.org_id
    user_b.role = UserRole.VIEWER
    db_session.commit()

    login_b = client.post(
        "/api/v1/auth/login",
        json={"email": "viewer@prog.com", "password": "Password123!"},
    ).json()
    headers_b = {"Authorization": f"Bearer {login_b['access_token']}"}

    # 4. Viewer can list and get project progress
    list_b = client.get("/api/v1/project-progress", headers=headers_b)
    assert list_b.status_code == status.HTTP_200_OK
    assert list_b.json()["total"] == 1

    get_b = client.get(f"/api/v1/project-progress/{item_id}", headers=headers_b)
    assert get_b.status_code == status.HTTP_200_OK
    assert get_b.json()["title"] == "Q3 Kubernetes Cluster Migration"

    # 5. Viewer attempting to create, update, or delete project progress should be rejected (403)
    assert client.post(
        "/api/v1/project-progress",
        json={"title": "Forbidden Tracker", "status": "blocked"},
        headers=headers_b,
    ).status_code == status.HTTP_403_FORBIDDEN

    assert client.put(
        f"/api/v1/project-progress/{item_id}",
        json={"progress_pct": 90},
        headers=headers_b,
    ).status_code == status.HTTP_403_FORBIDDEN

    assert client.delete(
        f"/api/v1/project-progress/{item_id}",
        headers=headers_b,
    ).status_code == status.HTTP_403_FORBIDDEN

    # 6. Admin updates & deletes item
    update_a = client.put(
        f"/api/v1/project-progress/{item_id}",
        json={"progress_pct": 100, "status": "completed"},
        headers=headers_a,
    )
    assert update_a.status_code == status.HTTP_200_OK
    assert update_a.json()["progress_pct"] == 100

    del_a = client.delete(f"/api/v1/project-progress/{item_id}", headers=headers_a)
    assert del_a.status_code == status.HTTP_204_NO_CONTENT


def test_project_progress_cross_tenant_isolation(client):
    # Org A
    res_a = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "Prog Org A", "email": "admin@prog-a.com", "password": "Password123!"},
    )
    headers_a = {"Authorization": f"Bearer {res_a.json()['access_token']}"}
    item_a = client.post(
        "/api/v1/project-progress",
        json={"title": "Org A Progress", "status": "in_progress", "progress_pct": 20},
        headers=headers_a,
    ).json()

    # Org B
    res_b = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "Prog Org B", "email": "admin@prog-b.com", "password": "Password123!"},
    )
    headers_b = {"Authorization": f"Bearer {res_b.json()['access_token']}"}

    item_id = item_a["id"]
    assert client.get(f"/api/v1/project-progress/{item_id}", headers=headers_b).status_code == status.HTTP_404_NOT_FOUND
    assert client.put(f"/api/v1/project-progress/{item_id}", json={"progress_pct": 50}, headers=headers_b).status_code == status.HTTP_404_NOT_FOUND
    assert client.delete(f"/api/v1/project-progress/{item_id}", headers=headers_b).status_code == status.HTTP_404_NOT_FOUND
