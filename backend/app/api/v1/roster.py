from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_admin, require_roles
from app.core.rate_limiter import rate_limit_mutations
from app.models.audit_log import record_audit_log
from app.models.team_member import TeamMember
from app.models.user import User, UserRole
from app.schemas.domain import (
    TeamMemberCreate,
    TeamMemberListResponse,
    TeamMemberRead,
    TeamMemberUpdate,
)

router = APIRouter(prefix="/team-members", tags=["Team Roster"])


@router.post(
    "",
    response_model=TeamMemberRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_mutations)],
    summary="Create Team Member",
    description="Adds a new member to the organization roster. Restricted to Admin role.",
)
def create_team_member(
    payload: TeamMemberCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    member = TeamMember(
        org_id=current_user.org_id,
        name=payload.name,
        email=payload.email,
        role=payload.role,
        status=payload.status,
    )
    db.add(member)
    db.flush()

    record_audit_log(
        db=db,
        org_id=current_user.org_id,
        actor_user_id=current_user.id,
        action="TEAM_MEMBER_CREATED",
        target_type="team_member",
        target_id=str(member.id),
        metadata_json={"name": member.name, "email": member.email, "role": member.role},
    )
    db.commit()
    db.refresh(member)
    return member


@router.get(
    "",
    response_model=TeamMemberListResponse,
    summary="List Team Members",
    description="Returns all roster members for the authenticated user's organization with pagination.",
)
def list_team_members(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(TeamMember).filter(TeamMember.org_id == current_user.org_id)
    total = query.count()
    items = query.order_by(TeamMember.created_at.desc()).offset(skip).limit(limit).all()
    return TeamMemberListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get(
    "/{member_id}",
    response_model=TeamMemberRead,
    summary="Get Team Member",
    description="Retrieves a specific team member by ID within the current organization.",
)
def get_team_member(
    member_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    member = (
        db.query(TeamMember)
        .filter(TeamMember.id == member_id, TeamMember.org_id == current_user.org_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team member not found")
    return member


@router.put(
    "/{member_id}",
    response_model=TeamMemberRead,
    dependencies=[Depends(rate_limit_mutations)],
    summary="Update Team Member",
    description="Updates a team member's details. Restricted to Admin role.",
)
def update_team_member(
    member_id: UUID,
    payload: TeamMemberUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    member = (
        db.query(TeamMember)
        .filter(TeamMember.id == member_id, TeamMember.org_id == current_user.org_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team member not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(member, field, value)

    record_audit_log(
        db=db,
        org_id=current_user.org_id,
        actor_user_id=current_user.id,
        action="TEAM_MEMBER_UPDATED",
        target_type="team_member",
        target_id=str(member.id),
        metadata_json=update_data,
    )
    db.commit()
    db.refresh(member)
    return member


@router.delete(
    "/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(rate_limit_mutations)],
    summary="Delete Team Member",
    description="Removes a team member from the roster. Restricted to Admin role.",
)
def delete_team_member(
    member_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    member = (
        db.query(TeamMember)
        .filter(TeamMember.id == member_id, TeamMember.org_id == current_user.org_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team member not found")

    db.delete(member)
    record_audit_log(
        db=db,
        org_id=current_user.org_id,
        actor_user_id=current_user.id,
        action="TEAM_MEMBER_DELETED",
        target_type="team_member",
        target_id=str(member_id),
        metadata_json={"email": member.email},
    )
    db.commit()
    return None
