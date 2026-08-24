import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, UUID, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import OrgScopedMixin


class ApiKey(Base, OrgScopedMixin):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    organization = relationship("Organization")
    user = relationship("User")
