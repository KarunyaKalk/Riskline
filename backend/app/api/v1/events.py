from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_user
from app.core.events import event_broadcaster
from app.models.user import User

router = APIRouter(prefix="/events", tags=["Real-Time Dashboard SSE"])


@router.get(
    "/stream",
    summary="Subscribe to Real-Time Org Events",
    description="Establishes a Server-Sent Events (SSE) connection broadcasting real-time changes, notes, and alerts strictly for the authenticated user's organization.",
)
def stream_realtime_events(
    current_user: User = Depends(get_current_user),
):
    return StreamingResponse(
        event_broadcaster.subscribe(current_user.org_id),
        media_type="text/event-stream",
    )
