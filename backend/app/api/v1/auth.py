import re
import uuid
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_org, get_current_user, get_db, require_admin, require_roles
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.models.team_member import TeamMember
from app.models.audit_log import record_audit_log
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    OrgOut,
    SignupRequest,
    UserMeResponse,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


def generate_slug(name: str) -> str:
    """Generate a clean URL slug from organization name."""
    s = name.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    s = re.sub(r"^-+|-+$", "", s)
    short_id = str(uuid.uuid4())[:8]
    return f"{s}-{short_id}" if s else f"org-{short_id}"


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        samesite="lax",
        secure=False,
    )


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, response: Response, db: Session = Depends(get_db)):
    """
    Creates a new Organization, Admin User, initial TeamMember, and records an AuditLog entry.
    """
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    try:
        # 1. Create Organization with generated slug
        org_slug = generate_slug(payload.org_name)
        org = Organization(name=payload.org_name, slug=org_slug, plan="free")
        db.add(org)
        db.flush()

        # 2. Create Admin User
        user = User(
            org_id=org.id,
            email=payload.email,
            hashed_password=hash_password(payload.password),
            role=UserRole.ADMIN,
            status="active",
        )
        db.add(user)
        db.flush()

        # 3. Create initial TeamMember roster entry
        team_member = TeamMember(
            org_id=org.id,
            user_id=user.id,
            name=payload.email.split("@")[0].capitalize(),
            email=payload.email,
            role="Organization Admin",
            status="active",
        )
        db.add(team_member)

        # 4. Record AuditLog entry for signup mutation from Day 1
        record_audit_log(
            db=db,
            org_id=org.id,
            actor_user_id=user.id,
            action="USER_SIGNUP",
            target_type="user",
            target_id=str(user.id),
            metadata_json={"email": user.email, "org_name": org.name},
        )

        db.commit()
        db.refresh(org)
        db.refresh(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create organization and admin user: {str(e)}",
        )

    # Generate JWT Tokens
    token_claims = {
        "sub": str(user.id),
        "org_id": str(user.org_id),
        "role": user.role.value if isinstance(user.role, UserRole) else str(user.role),
    }
    access_token = create_access_token(data=token_claims)
    refresh_token = create_refresh_token(data=token_claims)

    set_auth_cookies(response, access_token, refresh_token)

    return AuthResponse(
        user=UserOut.model_validate(user),
        organization=OrgOut.model_validate(org),
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """
    Authenticates user, logs AuditLog entry, returns JWT tokens & sets HttpOnly cookies.
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive or suspended",
        )

    org = db.query(Organization).filter(Organization.id == user.org_id).first()

    # Record AuditLog entry for login action
    record_audit_log(
        db=db,
        org_id=user.org_id,
        actor_user_id=user.id,
        action="USER_LOGIN",
        target_type="user",
        target_id=str(user.id),
        metadata_json={"email": user.email},
    )
    db.commit()

    token_claims = {
        "sub": str(user.id),
        "org_id": str(user.org_id),
        "role": user.role.value if isinstance(user.role, UserRole) else str(user.role),
    }
    access_token = create_access_token(data=token_claims)
    refresh_token = create_refresh_token(data=token_claims)

    set_auth_cookies(response, access_token, refresh_token)

    return AuthResponse(
        user=UserOut.model_validate(user),
        organization=OrgOut.model_validate(org),
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/logout")
def logout(response: Response):
    """
    Logs out user by clearing HttpOnly authentication cookies.
    """
    response.delete_cookie("access_token", samesite="lax")
    response.delete_cookie("refresh_token", samesite="lax")
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserMeResponse)
def get_me(
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
):
    """
    Returns current authenticated user and organization information.
    """
    return UserMeResponse(
        user=UserOut.model_validate(current_user),
        organization=OrgOut.model_validate(current_org),
    )


@router.get("/org-users", response_model=list[UserOut])
def get_org_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns all users belonging strictly to the authenticated user's organization.
    """
    users = db.query(User).filter(User.org_id == current_user.org_id).all()
    return [UserOut.model_validate(u) for u in users]


@router.get("/admin-only")
def admin_only_endpoint(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    RBAC Test Endpoint: strictly accessible only to Admin role users.
    """
    return {"message": "Access granted to admin", "user_id": str(current_user.id)}
