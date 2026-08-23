from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.rate_limiter import rate_limit_mutations
from app.models.audit_log import record_audit_log
from app.models.change import Change
from app.models.user import User, UserRole
from app.schemas.domain import (
    ChangeCreate,
    ChangeListResponse,
    ChangeRead,
    ChangeUpdate,
)

router = APIRouter(prefix="/changes", tags=["Changes"])


@router.post(
    "",
    response_model=ChangeRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_mutations)],
    summary="Create Deployment Change",
    description="Registers a new deployment or architectural change. Sets author_id strictly to the authenticated user.",
)
def create_change(
    payload: ChangeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    change = Change(
        org_id=current_user.org_id,
        title=payload.title,
        description=payload.description,
        status=payload.status,
        author_id=current_user.id,
        deployment_date=payload.deployment_date,
        risk_score=payload.risk_score,
        metadata_json=payload.metadata or {},
    )
    db.add(change)
    db.flush()

    record_audit_log(
        db=db,
        org_id=current_user.org_id,
        actor_user_id=current_user.id,
        action="CHANGE_CREATED",
        target_type="change",
        target_id=str(change.id),
        metadata_json={"title": change.title, "status": change.status},
    )
    db.commit()
    db.refresh(change)
    return change


@router.get(
    "",
    response_model=ChangeListResponse,
    summary="List Changes",
    description="Lists deployment change records with optional status filter, author filter, and pagination.",
)
def list_changes(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (pending, approved, deployed, rolled_back)"),
    author_id: Optional[UUID] = Query(None, description="Filter by author user ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Change).filter(Change.org_id == current_user.org_id)

    if status_filter:
        query = query.filter(Change.status == status_filter)
    if author_id:
        query = query.filter(Change.author_id == author_id)

    total = query.count()
    items = query.order_by(Change.created_at.desc()).offset(skip).limit(limit).all()
    return ChangeListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get(
    "/{change_id}",
    response_model=ChangeRead,
    summary="Get Change Details",
    description="Retrieves a specific change record by ID within the organization.",
)
def get_change(
    change_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    change = (
        db.query(Change)
        .filter(Change.id == change_id, Change.org_id == current_user.org_id)
        .first()
    )
    if not change:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change not found")
    return change


@router.put(
    "/{change_id}",
    response_model=ChangeRead,
    dependencies=[Depends(rate_limit_mutations)],
    summary="Update Change",
    description="Updates status or details of a change. Restricted to author, Engineer, or Admin roles.",
)
def update_change(
    change_id: UUID,
    payload: ChangeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    change = (
        db.query(Change)
        .filter(Change.id == change_id, Change.org_id == current_user.org_id)
        .first()
    )
    if not change:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change not found")

    is_admin_or_eng = current_user.role in [UserRole.ADMIN, UserRole.ENGINEER, "admin", "engineer"]
    if change.author_id != current_user.id and not is_admin_or_eng:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the author, Engineers, or Admins can modify this change record",
        )

    if payload.title is not None:
        change.title = payload.title
    if payload.description is not None:
        change.description = payload.description
    if payload.status is not None:
        change.status = payload.status
    if payload.deployment_date is not None:
        change.deployment_date = payload.deployment_date
    if payload.risk_score is not None:
        change.risk_score = payload.risk_score
    if payload.metadata is not None:
        change.metadata_json = payload.metadata

    record_audit_log(
        db=db,
        org_id=current_user.org_id,
        actor_user_id=current_user.id,
        action="CHANGE_UPDATED",
        target_type="change",
        target_id=str(change.id),
        metadata_json={"status": change.status, "title": change.title},
    )
    db.commit()
    db.refresh(change)
    return change


@router.delete(
    "/{change_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(rate_limit_mutations)],
    summary="Delete Change",
    description="Deletes a change record. Restricted to change author or Organization Admin.",
)
def delete_change(
    change_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    change = (
        db.query(Change)
        .filter(Change.id == change_id, Change.org_id == current_user.org_id)
        .first()
    )
    if not change:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change not found")

    is_admin = (current_user.role == UserRole.ADMIN or current_user.role == "admin")
    if change.author_id != current_user.id and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the author or an Organization Admin can delete this change record",
        )

    db.delete(change)
    record_audit_log(
        db=db,
        org_id=current_user.org_id,
        actor_user_id=current_user.id,
        action="CHANGE_DELETED",
        target_type="change",
        target_id=str(change_id),
        metadata_json={"title": change.title},
    )
    db.commit()
    return None
