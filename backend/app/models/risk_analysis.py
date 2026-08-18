import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, UUID, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import OrgScopedMixin


class RiskAnalysis(Base, OrgScopedMixin):
    __tablename__ = "risk_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    change_id = Column(UUID(as_uuid=True), ForeignKey("changes.id", ondelete="CASCADE"), nullable=False, index=True)
    technical_summary = Column(Text, nullable=False)
    business_summary = Column(Text, nullable=False)
    risk_level = Column(String(50), nullable=False, default="medium")
    recommendations_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    change = relationship("Change", back_populates="risk_analyses")
