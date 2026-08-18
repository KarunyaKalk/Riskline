import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy import Column, String, DateTime, UUID, ForeignKey, JSON
from sqlalchemy.orm import Session, relationship
from app.core.database import Base
from app.models.base import OrgScopedMixin


class AuditLog(Base, OrgScopedMixin):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(255), nullable=False, index=True)
    target_type = Column(String(100), nullable=False)
    target_id = Column(String(255), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    organization = relationship("Organization", back_populates="audit_logs")


def record_audit_log(
    db: Session,
    org_id: uuid.UUID,
    action: str,
    target_type: str,
    actor_user_id: Optional[uuid.UUID] = None,
    target_id: Optional[str] = None,
    metadata_json: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """
    Helper function to log system mutations into the audit_logs table.
    """
    log_entry = AuditLog(
        org_id=org_id,
        actor_user_id=actor_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        metadata_json=metadata_json,
    )
    db.add(log_entry)
    return log_entry
