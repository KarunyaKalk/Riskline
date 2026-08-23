import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, String, Text, DateTime, UUID, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import OrgScopedMixin


class Notification(Base, OrgScopedMixin):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), nullable=False, default="high_risk_alert")  # high_risk_alert, change_event
    is_read = Column(Boolean, nullable=False, default=False)
    target_url = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    organization = relationship("Organization", back_populates="notifications")
    user = relationship("User")


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    inapp_enabled = Column(Boolean, nullable=False, default=True)
    email_enabled = Column(Boolean, nullable=False, default=True)
    slack_enabled = Column(Boolean, nullable=False, default=True)
    min_risk_level = Column(String(50), nullable=False, default="high")  # high, critical
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User")
