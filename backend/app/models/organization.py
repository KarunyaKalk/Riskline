import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    plan = Column(String(50), nullable=False, default="free")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    team_members = relationship("TeamMember", back_populates="organization", cascade="all, delete-orphan")
    changes = relationship("Change", back_populates="organization", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="organization", cascade="all, delete-orphan")
    project_progresses = relationship("ProjectProgress", back_populates="organization", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="organization", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="organization", cascade="all, delete-orphan")
    invites = relationship("OrgInvite", back_populates="organization", cascade="all, delete-orphan")
