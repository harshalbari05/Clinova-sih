"""Clinical history interview schemas for Clinova Step 5B.

Defines the structured output contract between the LLM and the
interview engine, plus the enriched API response shape returned
to the frontend.

IMPORTANT — Safety principle:
    ExtractedClinicalInfo only holds patient-provided facts.
    The AI MUST NOT invent values. Unknown fields remain None.
    No diagnosis, treatment, or prescription fields exist here.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.ai_message import AIMessageResponse

__all__ = [
    "ClinicalInterviewAIResponse",
    "ExtractedClinicalInfo",
    "InterviewState",
    "InterviewSummary",
    "AIInterviewMessageResponse",
    "CLINICAL_SECTION_NAMES",
    "SECTION_PRIORITY_ORDER",
]

# ---------------------------------------------------------------------------
# Clinical section definitions
# ---------------------------------------------------------------------------

# Maps DB field names → human-readable section labels
CLINICAL_SECTION_NAMES: dict[str, str] = {
    "chief_complaint": "Chief Complaint",
    "history_of_present_illness": "History of Present Illness",
    "past_medical_history": "Past Medical History",
    "past_surgical_history": "Past Surgical History",
    "drug_history": "Drug History",
    "allergy_history": "Allergy History",
    "family_history": "Family History",
    "personal_history": "Personal History",
    "review_of_systems": "Review of Systems",
}

# Order in which sections are addressed during the interview
SECTION_PRIORITY_ORDER: list[str] = [
    "chief_complaint",
    "history_of_present_illness",
    "past_medical_history",
    "past_surgical_history",
    "drug_history",
    "allergy_history",
    "family_history",
    "personal_history",
    "review_of_systems",
]

# Core sections — interview requires at minimum these two
CORE_SECTIONS: frozenset[str] = frozenset(
    {"chief_complaint", "history_of_present_illness"}
)


# ---------------------------------------------------------------------------
# Structured output from the LLM
# ---------------------------------------------------------------------------


class ExtractedClinicalInfo(BaseModel):
    """Patient-provided clinical information extracted from the conversation.

    All fields are optional — the AI MUST only populate fields when the
    patient explicitly stated the information. Unknown fields remain None.

    SAFETY CONSTRAINTS enforced here:
    - No diagnosis field
    - No treatment / medication recommendation field
    - No prognosis field
    - Fields can only be str or None (no boolean shortcuts that imply certainty)
    """

    chief_complaint: str | None = None
    history_of_present_illness: str | None = None
    past_medical_history: str | None = None
    past_surgical_history: str | None = None
    drug_history: str | None = None
    allergy_history: str | None = None
    family_history: str | None = None
    personal_history: str | None = None
    review_of_systems: str | None = None

    model_config = ConfigDict(extra="ignore")  # reject unknown fields silently

    def has_any_content(self) -> bool:
        """True if at least one field has a non-None value."""
        return any(
            getattr(self, field) is not None
            for field in CLINICAL_SECTION_NAMES
        )

    def to_update_dict(self) -> dict[str, str | None]:
        """Return only fields that have content (non-None)."""
        return {
            k: v
            for k, v in self.model_dump().items()
            if v is not None
        }


class ClinicalInterviewAIResponse(BaseModel):
    """Structured output expected from the LLM for each interview turn.

    The LLM is instructed via system prompt to return this JSON structure.
    This schema is used for both:
    1. Parsing the LLM's raw JSON response.
    2. Validating that only safe, expected fields are present.

    SAFETY:
    - next_question is required — always ask one focused question.
    - interview_complete=True requires core sections to be filled
      (enforced in the service layer, not here).
    - extracted_information cannot contain diagnosis/prescription fields
      (ExtractedClinicalInfo model_config extra="ignore" handles this).
    """

    next_question: str = Field(
        ...,
        min_length=5,
        description="The next focused question to ask the patient. Required.",
    )
    extracted_information: ExtractedClinicalInfo | None = Field(
        default=None,
        description="Patient-provided clinical information extracted from this turn.",
    )
    missing_information: list[str] = Field(
        default_factory=list,
        description="List of information still missing from the clinical history.",
    )
    current_section: str | None = Field(
        default=None,
        description="The clinical section being addressed in this turn.",
    )
    section_complete: bool = Field(
        default=False,
        description="Whether the current section has been sufficiently addressed.",
    )
    interview_complete: bool = Field(
        default=False,
        description=(
            "Whether the AI believes the interview is complete. "
            "The service layer validates this — it cannot be accepted blindly."
        ),
    )

    @field_validator("current_section")
    @classmethod
    def validate_section(cls, v: str | None) -> str | None:
        if v is not None and v not in CLINICAL_SECTION_NAMES:
            # Accept gracefully — map unknown sections to None
            return None
        return v

    model_config = ConfigDict(extra="ignore")


# ---------------------------------------------------------------------------
# Interview state (derived — not stored in DB)
# ---------------------------------------------------------------------------


class InterviewState(BaseModel):
    """Runtime state of the clinical interview.

    Derived from the current ClinicalHistory record + message count.
    NOT stored as a separate DB record.
    """

    current_section: str
    completed_sections: list[str]
    missing_sections: list[str]
    interview_started: bool
    interview_complete: bool
    message_count: int

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# API response shape
# ---------------------------------------------------------------------------


class InterviewSummary(BaseModel):
    """Summary of the interview state returned to the client after each turn."""

    next_question: str
    current_section: str | None = None
    interview_complete: bool = False
    missing_information: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class AIInterviewMessageResponse(BaseModel):
    """Enriched response returned from POST /ai-sessions/{id}/messages.

    Contains both messages, interview state, and clinical history updates
    so the future frontend can update its UI in a single round-trip.

    Also exposes top-level fields (id, ai_session_id, sender, message, message_type, created_at)
    corresponding to the patient_message for 100% backward-compatibility with Step 4 clients.
    """

    # Top-level backwards compatibility fields (matching patient_message)
    id: uuid.UUID
    ai_session_id: uuid.UUID
    sender: str = "patient"
    message: str
    message_type: str = "text"
    created_at: datetime

    # Step 5B enriched response fields
    patient_message: AIMessageResponse
    ai_message: AIMessageResponse | None = None
    interview: InterviewSummary | None = None
    clinical_history_updates: dict[str, str | None] = Field(
        default_factory=dict,
        description="Clinical history fields updated in this interview turn.",
    )

    model_config = ConfigDict(from_attributes=True)

