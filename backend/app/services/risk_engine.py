import logging
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.events import event_broadcaster
from app.models.audit_log import record_audit_log
from app.models.change import Change
from app.models.risk_analysis import RiskAnalysis
from app.schemas.domain import RiskAnalysisRead
from app.services.embedding_service import index_change_text, search_similar_chunks
from app.services.llm_client import llm_client
from app.services.notification_service import trigger_high_risk_notifications

logger = logging.getLogger("risk_engine")


def format_risk_analysis_response(risk_record: RiskAnalysis, change: Change) -> RiskAnalysisRead:
    """Helper to convert database RiskAnalysis model to RiskAnalysisRead schema."""
    rec_data = risk_record.recommendations_json or {}
    recommendations_list = rec_data.get("recommendations", [])
    is_degraded = rec_data.get("is_degraded", False)

    return RiskAnalysisRead(
        id=risk_record.id,
        org_id=risk_record.org_id,
        change_id=risk_record.change_id,
        technical_summary=risk_record.technical_summary,
        business_summary=risk_record.business_summary,
        risk_level=risk_record.risk_level,
        risk_score=change.risk_score,
        recommendations=recommendations_list,
        is_degraded=is_degraded,
        created_at=risk_record.created_at,
    )


def run_risk_analysis_pipeline(db: Session, org_id: UUID, change_id: UUID) -> Optional[RiskAnalysisRead]:
    if isinstance(org_id, str):
        org_id = UUID(org_id)
    if isinstance(change_id, str):
        change_id = UUID(change_id)

    change = db.query(Change).filter(Change.id == change_id, Change.org_id == org_id).first()
    if not change:
        logger.error(f"Change {change_id} not found for org {org_id}")
        return None

    full_text = f"Title: {change.title}\nDescription:\n{change.description}"

    # 1. RAG Context Retrieval (Tenant-isolated)
    similar_chunks = search_similar_chunks(db, org_id, full_text, top_k=3)
    rag_context = ""
    if similar_chunks:
        rag_context = "\n".join([f"- [Sim: {score:.2f}] {chunk.chunk_text}" for chunk, score in similar_chunks])

    # 2. LLM Risk Assessment Generation
    analysis_output = llm_client.generate_risk_assessment(full_text, rag_context)

    # 3. Store RiskAnalysis record
    existing_analysis = db.query(RiskAnalysis).filter(
        RiskAnalysis.change_id == change_id, RiskAnalysis.org_id == org_id
    ).first()

    if existing_analysis:
        existing_analysis.technical_summary = analysis_output.technical_summary
        existing_analysis.business_summary = analysis_output.business_summary
        existing_analysis.risk_level = analysis_output.risk_level
        existing_analysis.recommendations_json = {
            "recommendations": analysis_output.recommendations,
            "is_degraded": analysis_output.is_degraded,
        }
        risk_record = existing_analysis
    else:
        risk_record = RiskAnalysis(
            org_id=org_id,
            change_id=change_id,
            technical_summary=analysis_output.technical_summary,
            business_summary=analysis_output.business_summary,
            risk_level=analysis_output.risk_level,
            recommendations_json={
                "recommendations": analysis_output.recommendations,
                "is_degraded": analysis_output.is_degraded,
            },
        )
        db.add(risk_record)

    # 4. Update Change record (Preserve specific user statuses like 'deployed' or 'approved')
    change.risk_score = analysis_output.risk_score
    if change.status in ["pending", "processing"]:
        change.status = "analyzed"

    # 5. Index change text into ChangeEmbedding table for future RAG queries
    indexed_chunks = index_change_text(db, org_id, change_id, full_text)

    # 6. Audit Log Recording
    record_audit_log(
        db=db,
        org_id=org_id,
        actor_user_id=change.author_id,
        action="RISK_ANALYSIS_COMPLETED",
        target_type="risk_analysis",
        target_id=str(risk_record.id),
        metadata_json={
            "risk_level": analysis_output.risk_level,
            "risk_score": analysis_output.risk_score,
            "indexed_chunks": indexed_chunks,
            "is_degraded": analysis_output.is_degraded,
        },
    )

    db.commit()
    db.refresh(risk_record)
    db.refresh(change)

    # 7. Trigger Live Event Broadcast & High Risk Notifications
    event_broadcaster.publish_sync(
        org_id=org_id,
        event_type="RISK_ANALYSIS_COMPLETED",
        payload={
            "change_id": str(change_id),
            "title": change.title,
            "risk_level": analysis_output.risk_level,
            "risk_score": analysis_output.risk_score,
        },
    )

    trigger_high_risk_notifications(
        db=db,
        org_id=org_id,
        change_id=change_id,
        change_title=change.title,
        risk_level=analysis_output.risk_level,
        risk_score=analysis_output.risk_score,
    )

    return format_risk_analysis_response(risk_record, change)
