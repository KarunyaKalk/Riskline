import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, UUID, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import OrgScopedMixin


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    ENGINEER = "engineer"
    BUSINESS_OPS = "business_ops"
    VIEWER = "viewer"


class User(Base, OrgScopedMixin):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(
        SQLEnum(UserRole, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=UserRole.ENGINEER,
    )
    status = Column(String(50), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    organization = relationship("Organization", back_populates="users")
    team_member = relationship("TeamMember", back_populates="user", uselist=False)
