import asyncio
import json
import logging
from typing import AsyncGenerator, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.chat_message import ChatMessage
from app.services.embedding_service import search_similar_chunks
from app.services.llm_client import llm_client

logger = logging.getLogger("chat_service")

# System prompts with few-shot examples for audience translation modes
SYSTEM_PROMPTS = {
    "technical": """You are DevOps Intelligence Assistant in TECHNICAL AUDIENCE mode.
Provide deep, precise technical details for SREs, DevOps engineers, and system architects. Include architectural impact, potential failure modes, rollback procedures, and CLI/API details.

Example 1 (Database Migration):
User: "What is the impact of dropping the legacy auth column?"
Assistant: "Dropping the legacy column requires an ALTER TABLE LOCK on PostgreSQL. If unindexed FK constraints exist, write-locks will stall incoming queries. Verify all active application connections are updated to the v2 schema prior to executing migration scripts."

Example 2 (Redis Upgrade):
User: "Is the Redis cluster upgrade safe?"
Assistant: "Upgrading Redis to 7.2 involves RDB persistence serialization updates. Ensure sentinel failover timeouts are set to >15s to prevent false-positive master re-elections during node rolling restarts."
""",
    "business": """You are DevOps Intelligence Assistant in BUSINESS/OPS AUDIENCE mode.
Translate complex engineering and infrastructure changes into plain language. Focus on business risk, customer experience impact, uptime SLAs, and team coordination. Avoid jargon.

Example 1 (Database Migration):
User: "What is the impact of dropping the legacy auth column?"
Assistant: "This update cleans up old system data storage. Customers should experience zero downtime, but login speeds will be monitored during the maintenance window."

Example 2 (Redis Upgrade):
User: "Is the Redis cluster upgrade safe?"
Assistant: "Yes, this routine performance upgrade boosts system speed. The engineering team will perform node maintenance with zero expected disruption to customer dashboard access."
""",
    "auto-detect": """You are DevOps Intelligence Assistant in AUTO-DETECT AUDIENCE mode.
Detect the user's intent. If the user asks technical or code questions, provide technical depth. If the user asks high-level business or operational questions, provide plain-language executive summaries.
""",
}


def build_chat_prompt(message: str, audience_mode: str, rag_context: str) -> str:
    sys_prompt = SYSTEM_PROMPTS.get(audience_mode, SYSTEM_PROMPTS["auto-detect"])
    full_prompt = f"{sys_prompt}\n\nHISTORICAL ORG CONTEXT:\n{rag_context or 'No prior relevant incident notes found.'}\n\nUSER QUESTION: {message}\n\nASSISTANT RESPONSE:"
    return full_prompt


async def stream_chat_response(
    db: Session,
    org_id: UUID,
    user_id: UUID,
    session_id: str,
    message: str,
    audience_mode: str = "auto-detect",
) -> AsyncGenerator[str, None]:
    """
    Generates a token-by-token streaming chat response (SSE formatted) grounded in org RAG context,
    persisting both user query and final assistant answer in ChatMessage table.
    """
    # 1. Save user query in ChatMessage table
    user_msg = ChatMessage(
        org_id=org_id,
        user_id=user_id,
        session_id=session_id,
        role="user",
        content=message,
    )
    db.add(user_msg)
    db.commit()

    # 2. Retrieve RAG historical context (Org-scoped)
    similar = search_similar_chunks(db, org_id, message, top_k=3)
    rag_context = ""
    if similar:
        rag_context = "\n".join([f"- {c.chunk_text}" for c, _ in similar])

    prompt = build_chat_prompt(message, audience_mode, rag_context)

    # 3. Stream response tokens
    # In mock mode, stream simulated token chunks for real-time frontend integration
    output = llm_client.generate_risk_assessment(message, rag_context)
    if audience_mode == "business":
        full_text = output.business_summary + "\n\nRecommendations:\n" + "\n".join([f"• {r}" for r in output.recommendations])
    elif audience_mode == "technical":
        full_text = output.technical_summary + f" (Risk Score: {output.risk_score}/10)" + "\n\nActions:\n" + "\n".join([f"1. {r}" for r in output.recommendations])
    else:
        full_text = f"**Executive Summary:** {output.business_summary}\n\n**Technical Details:** {output.technical_summary}"

    words = full_text.split(" ")
    collected_response = []

    for word in words:
        token = word + " "
        collected_response.append(token)
        chunk_json = json.dumps({"token": token, "session_id": session_id})
        yield f"data: {chunk_json}\n\n"
        await asyncio.sleep(0.03)  # Simulate smooth token streaming

    final_content = "".join(collected_response).strip()

    # 4. Save assistant response in ChatMessage table
    assistant_msg = ChatMessage(
        org_id=org_id,
        user_id=None,  # Assistant message
        session_id=session_id,
        role="assistant",
        content=final_content,
    )
    db.add(assistant_msg)
    db.commit()

    # Signal completion
    end_json = json.dumps({"done": True, "full_content": final_content})
    yield f"data: {end_json}\n\n"
