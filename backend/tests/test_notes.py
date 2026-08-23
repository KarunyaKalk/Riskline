import pytest
from fastapi import status


def test_notes_crud_tags_and_pagination(client):
    # Signup user
    signup_res = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "Notes Org", "email": "author@notes.com", "password": "Password123!"},
    )
    token = signup_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create notes with different tags
    note1 = client.post(
        "/api/v1/notes",
        json={"title": "DB Migration Plan", "content": "Postgres upgrade steps", "tags": ["decision", "blocker"]},
        headers=headers,
    ).json()

    note2 = client.post(
        "/api/v1/notes",
        json={"title": "RAG Pipeline Idea", "content": "Use pgvector embeddings", "tags": ["idea"]},
        headers=headers,
    ).json()

    # 2. List all notes
    list_all = client.get("/api/v1/notes", headers=headers).json()
    assert list_all["total"] == 2

    # 3. Filter notes by tag=blocker
    blocker_list = client.get("/api/v1/notes?tag=blocker", headers=headers).json()
    assert blocker_list["total"] == 1
    assert blocker_list["items"][0]["title"] == "DB Migration Plan"

    # 4. Pagination test (skip=0, limit=1)
    page1 = client.get("/api/v1/notes?skip=0&limit=1", headers=headers).json()
    assert page1["total"] == 2
    assert len(page1["items"]) == 1

    page2 = client.get("/api/v1/notes?skip=1&limit=1", headers=headers).json()
    assert page2["total"] == 2
    assert len(page2["items"]) == 1
    assert page1["items"][0]["id"] != page2["items"][0]["id"]

    # 5. Update note
    note_id = note1["id"]
    update_res = client.put(
        f"/api/v1/notes/{note_id}",
        json={"title": "Updated DB Migration Plan", "tags": ["decision", "resolved"]},
        headers=headers,
    )
    assert update_res.status_code == status.HTTP_200_OK
    assert update_res.json()["title"] == "Updated DB Migration Plan"

    # 6. Delete note
    del_res = client.delete(f"/api/v1/notes/{note_id}", headers=headers)
    assert del_res.status_code == status.HTTP_204_NO_CONTENT


def test_notes_author_and_admin_deletion_permissions(client, db_session):
    from app.models.user import User, UserRole

    # 1. Signup Admin (Alice)
    res_a = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "Notes Perm Org", "email": "alice@permnotes.com", "password": "Password123!"},
    )
    token_a = res_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Signup User B (Bob) via second signup for demo, then assign Bob to same org
    res_b = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "Bob Dummy Org", "email": "bob@permnotes.com", "password": "Password123!"},
    )
    token_b = res_b.json()["access_token"]
    user_a = db_session.query(User).filter(User.email == "alice@permnotes.com").first()
    user_b = db_session.query(User).filter(User.email == "bob@permnotes.com").first()

    # Move Bob to Alice's Org as ENGINEER
    user_b.org_id = user_a.org_id
    user_b.role = UserRole.ENGINEER
    db_session.commit()

    # Re-login Bob to get fresh token with updated org_id
    login_b = client.post(
        "/api/v1/auth/login",
        json={"email": "bob@permnotes.com", "password": "Password123!"},
    ).json()
    headers_b = {"Authorization": f"Bearer {login_b['access_token']}"}

    # 3. Bob creates a note
    bob_note = client.post(
        "/api/v1/notes",
        json={"title": "Bob Note", "content": "Secrets", "tags": ["question"]},
        headers=headers_b,
    ).json()
    note_id = bob_note["id"]

    # 4. Signup User C (Charlie) in same org as VIEWER
    res_c = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "Charlie Dummy Org", "email": "charlie@permnotes.com", "password": "Password123!"},
    )
    user_c = db_session.query(User).filter(User.email == "charlie@permnotes.com").first()
    user_c.org_id = user_a.org_id
    user_c.role = UserRole.VIEWER
    db_session.commit()

    login_c = client.post(
        "/api/v1/auth/login",
        json={"email": "charlie@permnotes.com", "password": "Password123!"},
    ).json()
    headers_c = {"Authorization": f"Bearer {login_c['access_token']}"}

    # Charlie (non-author, non-admin) trying to delete Bob's note should be rejected (403)
    del_c = client.delete(f"/api/v1/notes/{note_id}", headers=headers_c)
    assert del_c.status_code == status.HTTP_403_FORBIDDEN

    # Alice (Admin) can delete Bob's note
    del_a = client.delete(f"/api/v1/notes/{note_id}", headers=headers_a)
    assert del_a.status_code == status.HTTP_204_NO_CONTENT


def test_notes_cross_tenant_isolation(client):
    # Org A note
    res_a = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "Notes Org A", "email": "user@notes-a.com", "password": "Password123!"},
    )
    headers_a = {"Authorization": f"Bearer {res_a.json()['access_token']}"}
    note_a = client.post(
        "/api/v1/notes",
        json={"title": "Org A Confidential Note", "content": "Super Secret", "tags": ["decision"]},
        headers=headers_a,
    ).json()

    # Org B user
    res_b = client.post(
        "/api/v1/auth/signup",
        json={"org_name": "Notes Org B", "email": "user@notes-b.com", "password": "Password123!"},
    )
    headers_b = {"Authorization": f"Bearer {res_b.json()['access_token']}"}

    # Org B list notes should be empty
    list_b = client.get("/api/v1/notes", headers=headers_b).json()
    assert list_b["total"] == 0

    # Org B get/put/delete Org A note returns 404
    note_id = note_a["id"]
    assert client.get(f"/api/v1/notes/{note_id}", headers=headers_b).status_code == status.HTTP_404_NOT_FOUND
    assert client.put(f"/api/v1/notes/{note_id}", json={"title": "Hacked"}, headers=headers_b).status_code == status.HTTP_404_NOT_FOUND
    assert client.delete(f"/api/v1/notes/{note_id}", headers=headers_b).status_code == status.HTTP_404_NOT_FOUND
