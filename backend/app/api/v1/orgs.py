import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_admin
from app.core.rate_limiter import rate_limit_mutations
from app.core.security import hash_password
from app.models.audit_log import record_audit_log
from app.models.org_invite import OrgInvite
from app.models.organization import Organization
from app.models.team_member import TeamMember
from app.models.user import User, UserRole
from app.schemas.auth import UserOut
from app.schemas.domain import (
    InviteAcceptRequest,
    InviteCreate,
    InviteRead,
    RoleUpdatePayload,
)

router = APIRouter(prefix="/orgs", tags=["Organization Management"])


def check_invite_validity(invite: Optional[OrgInvite]) -> None:
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid invite token")
    if invite.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite token has already been used")
    
    expires = invite.expires_at
    now = datetime.now(timezone.utc) if expires.tzinfo is not None else datetime.now()
    if expires < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite token has expired")


@router.post(
    "/invites",
    response_model=InviteRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_mutations)],
    summary="Invite Teammate",
    description="Generates an invite token to invite a teammate by email. Restricted to Admin role.",
)
def create_invite(
    payload: InviteCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    # Check if user with this email already exists
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email is already registered",
        )

    # Generate secure 48-hour invite token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=48)

    invite = OrgInvite(
        org_id=current_user.org_id,
        email=payload.email,
        role=payload.role,
        token=token,
        status="pending",
        expires_at=expires_at,
    )
    db.add(invite)
    db.flush()

    # Log invite link to console (stub for email delivery)
    invite_url = f"http://localhost:5173/accept-invite?token={token}"
    print(f"[INVITE STUB] Teammate invite generated for {payload.email}: {invite_url}")

    record_audit_log(
        db=db,
        org_id=current_user.org_id,
        actor_user_id=current_user.id,
        action="USER_INVITED",
        target_type="org_invite",
        target_id=str(invite.id),
        metadata_json={"email": invite.email, "role": str(invite.role)},
    )
    db.commit()
    db.refresh(invite)
    return invite


@router.get(
    "/invites/{token}",
    response_model=InviteRead,
    summary="Get Invite Details",
    description="Retrieves details of an invite using its unique token for verification during signup.",
)
def get_invite_by_token(token: str, db: Session = Depends(get_db)):
    invite = db.query(OrgInvite).filter(OrgInvite.token == token).first()
    check_invite_validity(invite)
    return invite


@router.post(
    "/invites/accept",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_mutations)],
    summary="Accept Teammate Invite",
    description="Accepts an invite token and creates a user account attached to the inviting organization.",
)
def accept_invite(payload: InviteAcceptRequest, db: Session = Depends(get_db)):
    invite = db.query(OrgInvite).filter(OrgInvite.token == payload.token).first()
    check_invite_validity(invite)

    # Check if user already registered in the meantime
    existing_user = db.query(User).filter(User.email == invite.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User email already registered")

    # Create new User under invited org_id
    user = User(
        org_id=invite.org_id,
        email=invite.email,
        hashed_password=hash_password(payload.password),
        role=invite.role,
        status="active",
    )
    db.add(user)
    db.flush()

    # Create or update TeamMember entry
    display_name = payload.name or invite.email.split("@")[0].capitalize()
    team_member = (
        db.query(TeamMember)
        .filter(TeamMember.org_id == invite.org_id, TeamMember.email == invite.email)
        .first()
    )
    if team_member:
        team_member.user_id = user.id
        team_member.status = "active"
    else:
        team_member = TeamMember(
            org_id=invite.org_id,
            user_id=user.id,
            name=display_name,
            email=invite.email,
            role=str(invite.role).capitalize(),
            status="active",
        )
        db.add(team_member)

    invite.status = "accepted"

    record_audit_log(
        db=db,
        org_id=invite.org_id,
        actor_user_id=user.id,
        action="INVITE_ACCEPTED",
        target_type="user",
        target_id=str(user.id),
        metadata_json={"email": user.email, "role": str(user.role)},
    )
    db.commit()
    db.refresh(user)
    return user


@router.get(
    "/members",
    response_model=List[UserOut],
    summary="List Organization Members",
    description="Returns all user accounts belonging to the authenticated user's organization.",
)
def list_org_members(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(User).filter(User.org_id == current_user.org_id).all()


@router.put(
    "/members/{user_id}/role",
    response_model=UserOut,
    dependencies=[Depends(rate_limit_mutations)],
    summary="Change Member Role",
    description="Modifies a member's role within the organization. Restricted to Admin role.",
)
def update_member_role(
    user_id: UUID,
    payload: RoleUpdatePayload,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    target_user = (
        db.query(User)
        .filter(User.id == user_id, User.org_id == current_user.org_id)
        .first()
    )
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization member not found")

    # Prevent admin from demoting self if sole admin
    if target_user.id == current_user.id and payload.role != UserRole.ADMIN:
        admin_count = (
            db.query(User)
            .filter(User.org_id == current_user.org_id, User.role == UserRole.ADMIN)
            .count()
        )
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote yourself while you are the sole Organization Admin",
            )

    old_role = str(target_user.role)
    target_user.role = payload.role

    record_audit_log(
        db=db,
        org_id=current_user.org_id,
        actor_user_id=current_user.id,
        action="MEMBER_ROLE_UPDATED",
        target_type="user",
        target_id=str(target_user.id),
        metadata_json={"old_role": old_role, "new_role": str(payload.role)},
    )
    db.commit()
    db.refresh(target_user)
    return target_user


@router.delete(
    "/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(rate_limit_mutations)],
    summary="Remove Member",
    description="Removes a user account from the organization. Restricted to Admin role.",
)
def remove_member(
    user_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot remove your own user account from the organization",
        )

    target_user = (
        db.query(User)
        .filter(User.id == user_id, User.org_id == current_user.org_id)
        .first()
    )
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization member not found")

    db.delete(target_user)
    record_audit_log(
        db=db,
        org_id=current_user.org_id,
        actor_user_id=current_user.id,
        action="MEMBER_REMOVED",
        target_type="user",
        target_id=str(user_id),
        metadata_json={"email": target_user.email},
    )
    db.commit()
    return None
