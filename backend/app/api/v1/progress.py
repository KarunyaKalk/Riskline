from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.core.rate_limiter import rate_limit_mutations
from app.models.audit_log import record_audit_log
from app.models.project_progress import ProjectProgress
from app.models.user import User, UserRole
from app.schemas.domain import (
    ProjectProgressCreate,
    ProjectProgressListResponse,
    ProjectProgressRead,
    ProjectProgressUpdate,
)

router = APIRouter(prefix="/project-progress", tags=["Project Progress"])

# Require Admin or Engineer for mutating actions
require_progress_editor = require_roles(UserRole.ADMIN, UserRole.ENGINEER)


@router.post(
    "",
    response_model=ProjectProgressRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_mutations)],
    summary="Create Project Progress Item",
    description="Creates a project tracking item. Restricted to Admin or Engineer roles.",
)
def create_project_progress(
    payload: ProjectProgressCreate,
    current_user: User = Depends(require_progress_editor),
    db: Session = Depends(get_db),
):
    progress = ProjectProgress(
        org_id=current_user.org_id,
        title=payload.title,
        status=payload.status,
        progress_pct=payload.progress_pct,
        owner_id=payload.owner_id or current_user.id,
        target_date=payload.target_date,
    )
    db.add(progress)
    db.flush()

    record_audit_log(
        db=db,
        org_id=current_user.org_id,
        actor_user_id=current_user.id,
        action="PROJECT_PROGRESS_CREATED",
        target_type="project_progress",
        target_id=str(progress.id),
        metadata_json={"title": progress.title, "progress_pct": progress.progress_pct},
    )
    db.commit()
    db.refresh(progress)
    return progress


@router.get(
    "",
    response_model=ProjectProgressListResponse,
    summary="List Project Progress Items",
    description="Lists all project progress trackers for the organization. Accessible to all org members.",
)
def list_project_progress(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(ProjectProgress).filter(ProjectProgress.org_id == current_user.org_id)
    total = query.count()
    items = query.order_by(ProjectProgress.updated_at.desc()).offset(skip).limit(limit).all()
    return ProjectProgressListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get(
    "/{progress_id}",
    response_model=ProjectProgressRead,
    summary="Get Project Progress Item",
    description="Retrieves a specific project progress tracking record.",
)
def get_project_progress(
    progress_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    progress = (
        db.query(ProjectProgress)
        .filter(ProjectProgress.id == progress_id, ProjectProgress.org_id == current_user.org_id)
        .first()
    )
    if not progress:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project progress item not found")
    return progress


@router.put(
    "/{progress_id}",
    response_model=ProjectProgressRead,
    dependencies=[Depends(rate_limit_mutations)],
    summary="Update Project Progress Item",
    description="Updates status or percentage of a progress tracker. Restricted to Admin or Engineer roles.",
)
def update_project_progress(
    progress_id: UUID,
    payload: ProjectProgressUpdate,
    current_user: User = Depends(require_progress_editor),
    db: Session = Depends(get_db),
):
    progress = (
        db.query(ProjectProgress)
        .filter(ProjectProgress.id == progress_id, ProjectProgress.org_id == current_user.org_id)
        .first()
    )
    if not progress:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project progress item not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(progress, field, value)

    record_audit_log(
        db=db,
        org_id=current_user.org_id,
        actor_user_id=current_user.id,
        action="PROJECT_PROGRESS_UPDATED",
        target_type="project_progress",
        target_id=str(progress.id),
        metadata_json=update_data,
    )
    db.commit()
    db.refresh(progress)
    return progress


@router.delete(
    "/{progress_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(rate_limit_mutations)],
    summary="Delete Project Progress Item",
    description="Removes a project progress tracker. Restricted to Admin or Engineer roles.",
)
def delete_project_progress(
    progress_id: UUID,
    current_user: User = Depends(require_progress_editor),
    db: Session = Depends(get_db),
):
    progress = (
        db.query(ProjectProgress)
        .filter(ProjectProgress.id == progress_id, ProjectProgress.org_id == current_user.org_id)
        .first()
    )
    if not progress:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project progress item not found")

    db.delete(progress)
    record_audit_log(
        db=db,
        org_id=current_user.org_id,
        actor_user_id=current_user.id,
        action="PROJECT_PROGRESS_DELETED",
        target_type="project_progress",
        target_id=str(progress_id),
        metadata_json={"title": progress.title},
    )
    db.commit()
    return None
