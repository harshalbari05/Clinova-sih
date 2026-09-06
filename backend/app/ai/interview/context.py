"""Conversation context builder for the clinical interview engine.

This module fetches and formats the conversation history and current
clinical history for inclusion in the LLM request.

Key responsibilities:
  1. Fetch a bounded window of recent messages from ai_messages table.
  2. Convert DB message sender values to LLM role values:
       patient  → user
       ai       → assistant
       system   → skipped (system messages are not sent to the LLM as turns)
  3. Format the current ClinicalHistory as a readable JSON block for
     inclusion in the system prompt.
  4. Return a list[AIMessageInput] ready for AIRequest.messages.

Privacy guarantee:
  - Only fetches messages for the specific session_id.
  - The session_id's ownership is verified by the caller (ai_interview_service).
  - Messages from other patients' sessions are never fetched.

Context window:
  - Controlled by max_messages parameter (default from AI_INTERVIEW_MAX_HISTORY_MESSAGES).
  - Most recent messages are included; oldest are dropped when window is exceeded.
  - The current ClinicalHistory summary is always included in the system prompt
    regardless of context window size (it is compact JSON, not verbose chat).
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.schemas import AIMessageInput
from app.models.ai_message import AIMessage

if TYPE_CHECKING:
    from app.models.clinical_history import ClinicalHistory

logger = logging.getLogger(__name__)

__all__ = [
    "build_conversation_context",
    "format_clinical_history_for_prompt",
    "count_session_messages",
]

# Maps AIMessage.sender → LLM conversation role
_SENDER_TO_ROLE: dict[str, str] = {
    "patient": "user",
    "ai": "assistant",
}


async def build_conversation_context(
    db: AsyncSession,
    session_id: uuid.UUID,
    max_messages: int = 20,
) -> list[AIMessageInput]:
    """Fetch and convert recent conversation messages for the LLM.

    Retrieves up to `max_messages` most recent messages from this session,
    converts sender values to LLM roles, and returns them in chronological
    order (oldest first).

    System messages (sender='system') are excluded — they are internal
    metadata and not meaningful turns for the LLM.

    Args:
        db: Active async database session.
        session_id: UUID of the AI session to fetch messages from.
        max_messages: Maximum number of messages to include (default 20).

    Returns:
        Chronologically ordered list of AIMessageInput.
    """
    from sqlalchemy import func

    # Count total relevant messages
    count_stmt = select(func.count()).where(
        AIMessage.ai_session_id == session_id,
        AIMessage.sender.in_(["patient", "ai"]),  # exclude system turns
    )
    total: int = (await db.execute(count_stmt)).scalar_one()

    # Calculate offset to get the latest max_messages in chronological order
    offset = max(0, total - max_messages)

    stmt = (
        select(AIMessage)
        .where(
            AIMessage.ai_session_id == session_id,
            AIMessage.sender.in_(["patient", "ai"]),
        )
        .order_by(AIMessage.created_at.asc())
        .offset(offset)
        .limit(max_messages)
    )
    rows = (await db.execute(stmt)).scalars().all()

    messages: list[AIMessageInput] = []
    for msg in rows:
        role = _SENDER_TO_ROLE.get(msg.sender)
        if role is None:
            continue  # skip any unexpected sender values
        messages.append(AIMessageInput(role=role, content=msg.message))

    logger.debug(
        "Built conversation context: %d/%d messages for session %s.",
        len(messages),
        max_messages,
        session_id,
    )
    return messages


def format_clinical_history_for_prompt(
    history: "ClinicalHistory | None",
) -> str:
    """Format the current ClinicalHistory as a compact JSON block.

    This is embedded in the system prompt so the LLM knows what
    information has already been collected and what is still missing.
    Only clinical content fields are included — no IDs, timestamps, etc.

    None values are included as null so the LLM can see explicitly what
    is missing and avoid asking for information already captured.

    Args:
        history: The ClinicalHistory ORM object, or None if not yet created.

    Returns:
        A compact JSON string suitable for embedding in the system prompt.
    """
    if history is None:
        data: dict[str, str | None] = {
            "chief_complaint": None,
            "history_of_present_illness": None,
            "past_medical_history": None,
            "past_surgical_history": None,
            "drug_history": None,
            "allergy_history": None,
            "family_history": None,
            "personal_history": None,
            "review_of_systems": None,
        }
    else:
        data = {
            "chief_complaint": history.chief_complaint,
            "history_of_present_illness": history.history_of_present_illness,
            "past_medical_history": history.past_medical_history,
            "past_surgical_history": history.past_surgical_history,
            "drug_history": history.drug_history,
            "allergy_history": history.allergy_history,
            "family_history": history.family_history,
            "personal_history": history.personal_history,
            "review_of_systems": history.review_of_systems,
        }

    return json.dumps(data, ensure_ascii=False, indent=2)


async def count_session_messages(
    db: AsyncSession,
    session_id: uuid.UUID,
) -> int:
    """Return the total number of messages in the session.

    Used to derive InterviewState.message_count.
    """
    from sqlalchemy import func
    stmt = select(func.count()).where(AIMessage.ai_session_id == session_id)
    result = await db.execute(stmt)
    return result.scalar_one()
