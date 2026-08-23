import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, UUID, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import OrgScopedMixin
from app.models.user import UserRole


class OrgInvite(Base, OrgScopedMixin):
    __tablename__ = "org_invites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, index=True)
    role = Column(
        SQLEnum(UserRole, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=UserRole.ENGINEER,
    )
    token = Column(String(255), nullable=False, unique=True, index=True)
    status = Column(String(50), nullable=False, default="pending")  # pending, accepted, expired
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    organization = relationship("Organization")
