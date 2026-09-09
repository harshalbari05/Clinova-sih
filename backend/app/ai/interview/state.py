"""Interview state derivation for Clinova Step 5B.

Derives the current InterviewState purely from the existing
ClinicalHistory ORM object and the conversation message count.
No new DB table or column is required.

The state determines:
- Which section is currently being addressed
- Which sections are complete (have non-None content)
- Which sections are still missing
- Whether the interview has started and/or is complete

This module has NO database queries — it is a pure computation
over data already retrieved by the caller.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.ai.interview.schemas import (
    CORE_SECTIONS,
    SECTION_PRIORITY_ORDER,
    InterviewState,
)

if TYPE_CHECKING:
    from app.models.clinical_history import ClinicalHistory

__all__ = [
    "derive_interview_state",
    "is_interview_completable",
]


def derive_interview_state(
    clinical_history: "ClinicalHistory | None",
    message_count: int,
) -> InterviewState:
    """Derive the current interview state from existing data.

    Computes which sections are complete and what section to address next,
    using the section priority order. Makes no database calls.

    Args:
        clinical_history: The ClinicalHistory ORM object for this consultation,
                          or None if not yet created.
        message_count:    Total number of messages in the session so far.

    Returns:
        InterviewState reflecting current progress.
    """
    completed: list[str] = []
    missing: list[str] = []

    # Number of patient messages submitted so far (turns taken)
    patient_turns = max(0, message_count // 2)

    for idx, section in enumerate(SECTION_PRIORITY_ORDER):
        value = None
        if clinical_history is not None:
            value = getattr(clinical_history, section, None)

        if (value and str(value).strip()) or (idx < patient_turns):
            completed.append(section)
        else:
            missing.append(section)

    # Current section = first missing in priority order
    current_section = missing[0] if missing else SECTION_PRIORITY_ORDER[-1]

    # Interview complete when no missing sections remain
    all_complete = len(missing) == 0

    return InterviewState(
        current_section=current_section,
        completed_sections=completed,
        missing_sections=missing,
        interview_started=message_count > 0,
        interview_complete=all_complete,
        message_count=message_count,
    )


def is_interview_completable(
    clinical_history: "ClinicalHistory | None",
    ai_says_complete: bool,
    is_fallback: bool = False,
) -> bool:
    """Determine if the interview can be safely marked as complete.

    The AI's own `interview_complete` flag is a signal, not a mandate.
    We validate that at minimum the core sections are present before
    allowing the session to transition to 'completed'.

    In adaptive fallback mode, completion is driven by the rule-based
    state engine covering all clinical sections.

    This prevents the LLM from prematurely ending an interview after
    just one turn or when critical information is missing.

    Args:
        clinical_history: Current ClinicalHistory or None.
        ai_says_complete: Whether the AI flagged interview_complete=True.
        is_fallback:      Whether running in adaptive intake engine fallback mode.

    Returns:
        True only if both the AI signals completion AND core fields are present
        (or adaptive fallback has completed all sections).
    """
    if not ai_says_complete:
        return False

    if is_fallback:
        return True

    if clinical_history is None:
        return False

    # Check all core sections have content
    for section in CORE_SECTIONS:
        value = getattr(clinical_history, section, None)
        if not (value and str(value).strip()):
            return False

    return True
