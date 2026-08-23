from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.chat_message import ChatMessage
from app.models.user import User
from app.schemas.domain import ChatHistoryResponse, ChatMessageRead, ChatMessageSend
from app.services.chat_service import stream_chat_response

router = APIRouter(prefix="/chat", tags=["Chatbot & RAG Assistant"])


@router.post(
    "/stream",
    summary="Stream Chatbot Response",
    description="Sends a chat message prompt and streams token-by-token responses using Server-Sent Events (SSE), grounded in org RAG context.",
)
def send_chat_message_stream(
    payload: ChatMessageSend,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return StreamingResponse(
        stream_chat_response(
            db=db,
            org_id=current_user.org_id,
            user_id=current_user.id,
            session_id=payload.session_id,
            message=payload.message,
            audience_mode=payload.audience,
        ),
        media_type="text/event-stream",
    )


@router.get(
    "/history",
    response_model=ChatHistoryResponse,
    summary="Get Chat History",
    description="Retrieves persistent chat message history for a specific org session.",
)
def get_chat_history(
    session_id: str = Query("main", description="Session ID (default: main)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = (
        db.query(ChatMessage)
        .filter(ChatMessage.org_id == current_user.org_id, ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return ChatHistoryResponse(items=items, total=total, skip=skip, limit=limit)
