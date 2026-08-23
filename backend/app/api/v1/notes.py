from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import String, cast
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.rate_limiter import rate_limit_mutations
from app.models.audit_log import record_audit_log
from app.models.note import Note
from app.models.user import User, UserRole
from app.schemas.domain import (
    NoteCreate,
    NoteListResponse,
    NoteRead,
    NoteUpdate,
)

router = APIRouter(prefix="/notes", tags=["Notes & Brainstorm"])


@router.post(
    "",
    response_model=NoteRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_mutations)],
    summary="Create Note",
    description="Creates a new brainstorm note or decision record. Author is automatically assigned to current user.",
)
def create_note(
    payload: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    note = Note(
        org_id=current_user.org_id,
        title=payload.title,
        content=payload.content,
        author_id=current_user.id,
        tags_json=payload.tags or [],
    )
    db.add(note)
    db.flush()

    record_audit_log(
        db=db,
        org_id=current_user.org_id,
        actor_user_id=current_user.id,
        action="NOTE_CREATED",
        target_type="note",
        target_id=str(note.id),
        metadata_json={"title": note.title, "tags": note.tags_json},
    )
    db.commit()
    db.refresh(note)
    return note


@router.get(
    "",
    response_model=NoteListResponse,
    summary="List Notes",
    description="Lists brainstorm notes with optional tag filtering, author filtering, and pagination.",
)
def list_notes(
    tag: Optional[str] = Query(None, description="Filter notes containing a specific tag (e.g. blocker, idea)"),
    author_id: Optional[UUID] = Query(None, description="Filter notes created by a specific user ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Note).filter(Note.org_id == current_user.org_id)

    if author_id:
        query = query.filter(Note.author_id == author_id)

    all_notes = query.order_by(Note.created_at.desc()).all()

    # Filter by tag in Python to guarantee cross-database compatibility (PostgreSQL & SQLite)
    if tag:
        all_notes = [n for n in all_notes if n.tags_json and tag in n.tags_json]

    total = len(all_notes)
    items = all_notes[skip : skip + limit]

    return NoteListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get(
    "/{note_id}",
    response_model=NoteRead,
    summary="Get Note",
    description="Retrieves details of a specific note within the user's organization.",
)
def get_note(
    note_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    note = (
        db.query(Note)
        .filter(Note.id == note_id, Note.org_id == current_user.org_id)
        .first()
    )
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return note


@router.put(
    "/{note_id}",
    response_model=NoteRead,
    dependencies=[Depends(rate_limit_mutations)],
    summary="Update Note",
    description="Updates a note's title, content, or tags. Restricted to the author or Organization Admin.",
)
def update_note(
    note_id: UUID,
    payload: NoteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    note = (
        db.query(Note)
        .filter(Note.id == note_id, Note.org_id == current_user.org_id)
        .first()
    )
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    # Author or Admin permission check
    is_admin = (current_user.role == UserRole.ADMIN or current_user.role == "admin")
    if note.author_id != current_user.id and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the note author or an Organization Admin can modify this note",
        )

    if payload.title is not None:
        note.title = payload.title
    if payload.content is not None:
        note.content = payload.content
    if payload.tags is not None:
        note.tags_json = payload.tags

    record_audit_log(
        db=db,
        org_id=current_user.org_id,
        actor_user_id=current_user.id,
        action="NOTE_UPDATED",
        target_type="note",
        target_id=str(note.id),
        metadata_json={"title": note.title, "tags": note.tags_json},
    )
    db.commit()
    db.refresh(note)
    return note


@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(rate_limit_mutations)],
    summary="Delete Note",
    description="Deletes a note. Restricted to the note author or Organization Admin.",
)
def delete_note(
    note_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    note = (
        db.query(Note)
        .filter(Note.id == note_id, Note.org_id == current_user.org_id)
        .first()
    )
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    is_admin = (current_user.role == UserRole.ADMIN or current_user.role == "admin")
    if note.author_id != current_user.id and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the note author or an Organization Admin can delete this note",
        )

    db.delete(note)
    record_audit_log(
        db=db,
        org_id=current_user.org_id,
        actor_user_id=current_user.id,
        action="NOTE_DELETED",
        target_type="note",
        target_id=str(note_id),
        metadata_json={"title": note.title},
    )
    db.commit()
    return None
