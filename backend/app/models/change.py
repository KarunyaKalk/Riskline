import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Float, DateTime, UUID, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import OrgScopedMixin


class Change(Base, OrgScopedMixin):
    __tablename__ = "changes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # pending, processing, analyzed, deployed, rolled_back
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    deployment_date = Column(DateTime(timezone=True), nullable=True)
    risk_score = Column(Float, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    organization = relationship("Organization", back_populates="changes")
    risk_analyses = relationship("RiskAnalysis", back_populates="change", cascade="all, delete-orphan")
    embeddings = relationship("ChangeEmbedding", back_populates="change", cascade="all, delete-orphan")
