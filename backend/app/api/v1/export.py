import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.api_key import ApiKey
from app.models.audit_log import record_audit_log
from app.models.change import Change
from app.models.organization import Organization
from app.models.project_progress import ProjectProgress
from app.models.risk_analysis import RiskAnalysis
from app.models.user import User, UserRole

router = APIRouter(prefix="/export", tags=["Power BI & Analytics Export"])


class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Key description e.g. Power BI Desktop Key")


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    api_key: str
    created_at: datetime


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


@router.post(
    "/api-keys",
    response_model=ApiKeyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Issue Power BI API Key",
    description="Issues a read-only API Key for Power BI integrations. Restricted to Organization Admin.",
)
def issue_api_key(
    payload: ApiKeyCreate,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    raw_key = f"rk_live_{secrets.token_urlsafe(24)}"
    key_hash = hash_api_key(raw_key)

    api_key = ApiKey(
        org_id=current_user.org_id,
        user_id=current_user.id,
        name=payload.name,
        key_hash=key_hash,
    )
    db.add(api_key)
    db.flush()

    record_audit_log(
        db=db,
        org_id=current_user.org_id,
        actor_user_id=current_user.id,
        action="API_KEY_ISSUED",
        target_type="api_key",
        target_id=str(api_key.id),
        metadata_json={"name": payload.name},
    )
    db.commit()
    db.refresh(api_key)

    return ApiKeyResponse(
        id=str(api_key.id),
        name=api_key.name,
        api_key=raw_key,
        created_at=api_key.created_at,
    )


@router.get(
    "/power-bi",
    summary="Power BI Export Feed",
    description="API-key authenticated read-only endpoint returning tabular change, risk, and progress analytics for Power BI Desktop.",
)
def export_power_bi_data(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    api_key: Optional[str] = Query(None, description="API Key via query parameter"),
    db: Session = Depends(get_db),
):
    provided_key = x_api_key or api_key
    if not provided_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key. Provide via 'X-API-Key' header or '?api_key=...' query parameter.",
        )

    key_hash = hash_api_key(provided_key.strip())
    api_key_record = db.query(ApiKey).filter(ApiKey.key_hash == key_hash).first()
    if not api_key_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API Key.",
        )

    org_id = api_key_record.org_id
    org = db.query(Organization).filter(Organization.id == org_id).first()

    # Query tenant-scoped data
    changes = db.query(Change).filter(Change.org_id == org_id).all()
    progresses = db.query(ProjectProgress).filter(ProjectProgress.org_id == org_id).all()
    analyses = db.query(RiskAnalysis).filter(RiskAnalysis.org_id == org_id).all()

    analysis_map = {a.change_id: a for a in analyses}

    change_list = []
    for c in changes:
        analysis = analysis_map.get(c.id)
        change_list.append({
            "change_id": str(c.id),
            "title": c.title,
            "description": c.description,
            "status": c.status,
            "author_id": str(c.author_id) if c.author_id else None,
            "deployment_date": c.deployment_date.isoformat() if c.deployment_date else None,
            "risk_score": c.risk_score,
            "risk_level": analysis.risk_level if analysis else ("high" if (c.risk_score or 0) >= 7.0 else "medium"),
            "technical_summary": analysis.technical_summary if analysis else None,
            "business_summary": analysis.business_summary if analysis else None,
            "created_at": c.created_at.isoformat(),
        })

    total_changes = len(changes)
    high_risk_count = sum(1 for c in changes if (c.risk_score or 0) >= 7.0)
    avg_score = (sum(c.risk_score or 0.0 for c in changes) / total_changes) if total_changes > 0 else 0.0

    return {
        "organization": org.name if org else "Unknown",
        "org_id": str(org_id),
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_changes": total_changes,
            "avg_risk_score": round(avg_score, 2),
            "high_risk_count": high_risk_count,
            "deployed_count": sum(1 for c in changes if c.status == "deployed"),
        },
        "changes": change_list,
        "milestones": [
            {
                "milestone_id": str(p.id),
                "title": p.title,
                "status": p.status,
                "progress_pct": p.progress_pct,
                "target_date": p.target_date.isoformat() if p.target_date else None,
            }
            for p in progresses
        ],
    }
