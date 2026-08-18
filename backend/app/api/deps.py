from typing import Callable, Generator, List, Optional, Union
from uuid import UUID
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import decode_access_token
from app.models.organization import Organization
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def extract_token_from_request(
    request: Request, bearer_token: Optional[str] = Depends(oauth2_scheme)
) -> Optional[str]:
    """
    Extract access token from Bearer header or HttpOnly access_token cookie.
    """
    if bearer_token:
        return bearer_token
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token
    return None


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(extract_token_from_request),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or missing token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    user_id_str: Optional[str] = payload.get("sub")
    org_id_str: Optional[str] = payload.get("org_id")

    if not user_id_str or not org_id_str:
        raise credentials_exception

    try:
        user_id = UUID(user_id_str)
        org_id = UUID(org_id_str)
    except ValueError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id, User.org_id == org_id).first()
    if not user or user.status != "active":
        raise credentials_exception

    return user


def get_current_org(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Organization:
    org = db.query(Organization).filter(Organization.id == current_user.org_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return org


class RoleChecker:
    """
    Dependency factory to check if the authenticated user possesses one of the allowed roles.
    """

    def __init__(self, allowed_roles: List[Union[UserRole, str]]):
        self.allowed_roles = [r.value if isinstance(r, UserRole) else str(r) for r in allowed_roles]

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        user_role_str = current_user.role.value if isinstance(current_user.role, UserRole) else str(current_user.role)
        if user_role_str not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{user_role_str}' lacks permission to access this resource",
            )
        return current_user


def require_roles(*roles: Union[UserRole, str]) -> RoleChecker:
    return RoleChecker(list(roles))


require_admin = require_roles(UserRole.ADMIN)
