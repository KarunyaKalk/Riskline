from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.domain import AuditLogListResponse

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get(
    "",
    response_model=AuditLogListResponse,
    summary="List Audit Logs",
    description="Lists security and mutation audit log entries for the organization with pagination and action filtering.",
)
def list_audit_logs(
    action: Optional[str] = Query(None, description="Filter logs by action name (e.g. USER_LOGIN, CHANGE_CREATED)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(AuditLog).filter(AuditLog.org_id == current_user.org_id)

    if action:
        query = query.filter(AuditLog.action == action)

    total = query.count()
    items = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    return AuditLogListResponse(items=items, total=total, skip=skip, limit=limit)
