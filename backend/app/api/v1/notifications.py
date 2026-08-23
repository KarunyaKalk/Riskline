from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.notification import Notification, NotificationPreference
from app.models.user import User
from app.schemas.domain import (
    NotificationListResponse,
    NotificationPreferenceRead,
    NotificationPreferenceUpdate,
    NotificationRead,
)
from app.services.notification_service import get_or_create_user_preference

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "",
    response_model=NotificationListResponse,
    summary="List User Notifications",
    description="Lists in-app notifications for the authenticated user, including unread count.",
)
def list_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Notification).filter(
        Notification.org_id == current_user.org_id, Notification.user_id == current_user.id
    )
    total = query.count()
    unread_count = query.filter(Notification.is_read == False).count()
    items = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
    return NotificationListResponse(items=items, unread_count=unread_count, total=total, skip=skip, limit=limit)


@router.put(
    "/{notification_id}/read",
    response_model=NotificationRead,
    summary="Mark Notification as Read",
    description="Marks a specific in-app notification as read.",
)
def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notif = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.org_id == current_user.org_id,
            Notification.user_id == current_user.id,
        )
        .first()
    )
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif


@router.get(
    "/preferences",
    response_model=NotificationPreferenceRead,
    summary="Get Notification Preferences",
    description="Retrieves the user's notification preferences.",
)
def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pref = get_or_create_user_preference(db, current_user.id)
    return pref


@router.put(
    "/preferences",
    response_model=NotificationPreferenceRead,
    summary="Update Notification Preferences",
    description="Updates the user's notification delivery settings (in-app, email, slack).",
)
def update_notification_preferences(
    payload: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pref = get_or_create_user_preference(db, current_user.id)

    if payload.inapp_enabled is not None:
        pref.inapp_enabled = payload.inapp_enabled
    if payload.email_enabled is not None:
        pref.email_enabled = payload.email_enabled
    if payload.slack_enabled is not None:
        pref.slack_enabled = payload.slack_enabled
    if payload.min_risk_level is not None:
        pref.min_risk_level = payload.min_risk_level

    db.commit()
    db.refresh(pref)
    return pref
