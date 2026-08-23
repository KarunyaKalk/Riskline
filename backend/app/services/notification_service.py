import logging
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.events import event_broadcaster
from app.models.notification import Notification, NotificationPreference
from app.models.user import User

logger = logging.getLogger("notification_service")


def get_or_create_user_preference(db: Session, user_id: UUID) -> NotificationPreference:
    pref = db.query(NotificationPreference).filter(NotificationPreference.user_id == user_id).first()
    if not pref:
        pref = NotificationPreference(
            user_id=user_id,
            inapp_enabled=True,
            email_enabled=True,
            slack_enabled=True,
            min_risk_level="high",
        )
        db.add(pref)
        db.flush()
    return pref


def trigger_high_risk_notifications(
    db: Session, org_id: UUID, change_id: UUID, change_title: str, risk_level: str, risk_score: float
) -> List[Notification]:
    """
    Triggers in-app, email, and Slack webhook notifications when a high or critical risk deployment is detected.
    """
    if risk_level not in ["high", "critical"] and risk_score < 7.0:
        return []

    org_users = db.query(User).filter(User.org_id == org_id, User.status == "active").all()
    created_notifications = []

    title = f"High Risk Deployment Alert [{risk_level.upper()}]"
    message = f"Change '{change_title}' evaluated at risk score {risk_score:.1f}/10.0 ({risk_level.upper()}). Review required."
    target_url = f"/changes/{change_id}"

    for user in org_users:
        pref = get_or_create_user_preference(db, user.id)

        # 1. In-App Notification
        if pref.inapp_enabled:
            n = Notification(
                org_id=org_id,
                user_id=user.id,
                title=title,
                message=message,
                type="high_risk_alert",
                target_url=target_url,
            )
            db.add(n)
            created_notifications.append(n)

        # 2. Email Delivery Stub
        if pref.email_enabled:
            print(f"[EMAIL NOTIFICATION STUB] To: {user.email} | Subject: {title} | Body: {message}")

        # 3. Slack Webhook Stub
        if pref.slack_enabled:
            print(f"[SLACK WEBHOOK STUB] Channel: #devops-alerts | Alert: {title} - {message}")

    db.commit()

    # Broadcast live real-time notification event via SSE
    event_broadcaster.publish_sync(
        org_id,
        "HIGH_RISK_NOTIFICATION",
        {
            "change_id": str(change_id),
            "title": title,
            "message": message,
            "risk_level": risk_level,
            "risk_score": risk_score,
        },
    )

    return created_notifications
