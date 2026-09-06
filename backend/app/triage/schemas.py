"""Triage schemas for Clinova Step 6: Red-Flag Detection & Triage.

Defines the contract for triage findings, urgency categorization,
and alert outputs for clinician decision support.

SAFETY PRINCIPLE:
    - No diagnosis fields exist here.
    - No treatment or prescription recommendations exist here.
    - All categories represent clinical findings and safety review levels.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TriageUrgency(str, enum.Enum):
    """Urgency level determined for a patient's reported symptoms.

    NORMAL:
        No defined red-flag finding detected. Standard workflow.
    URGENT:
        Concerning finding requiring prompt clinician review, but not
        necessarily immediate emergency escalation.
    EMERGENCY_REVIEW:
        A high-priority red-flag pattern is explicitly present.
        Surfaced immediately to clinical staff for urgent attention.
    """

    NORMAL = "NORMAL"
    URGENT = "URGENT"
    EMERGENCY_REVIEW = "EMERGENCY_REVIEW"


class TriageCategory(str, enum.Enum):
    """Broad categories for triage and red-flag classification."""

    CARDIOVASCULAR_CHEST = "cardiovascular_chest"
    RESPIRATORY = "respiratory"
    NEUROLOGICAL = "neurological"
    BLEEDING = "bleeding"
    SEVERE_PAIN = "severe_pain"
    ANAPHYLAXIS = "anaphylaxis"
    ALTERED_CONSCIOUSNESS = "altered_consciousness"
    SELF_HARM = "self_harm"
    PREGNANCY_URGENT = "pregnancy_urgent"
    GENERAL = "general"


class TriageFinding(BaseModel):
    """A specific evidence-backed finding extracted from patient-reported data.

    SAFETY:
        - 'code': standard machine-readable identifier (e.g. 'CHEST_PAIN_CRUSHING').
        - 'present': boolean indicating whether evidence supports this finding.
        - 'evidence': literal text/quote from patient message or clinical history.
        - No disease names or treatment directives.
    """

    code: str
    category: TriageCategory
    severity: str = "medium"  # low, medium, high, critical
    present: bool = True
    evidence: str
    confidence: float = 1.0

    model_config = ConfigDict(extra="ignore")


class TriageResult(BaseModel):
    """Consolidated result of red-flag detection and triage analysis."""

    consultation_id: uuid.UUID
    has_red_flags: bool
    urgency: TriageUrgency
    findings: list[TriageFinding] = Field(default_factory=list)
    requires_immediate_attention: bool = False
    explanation_for_clinician: str
    patient_safety_guidance: str | None = None
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    source: str = "DETERMINISTIC_RULES"

    model_config = ConfigDict(from_attributes=True)


class AITriageFindingItem(BaseModel):
    """Schema for individual findings extracted via LLM assistance."""

    finding: str
    category: str
    present: bool = True
    evidence: str
    confidence: float = 1.0

    model_config = ConfigDict(extra="ignore")


class AITriageExtractionResponse(BaseModel):
    """Structured output expected from the LLM when executing TaskType.TRIAGE.

    The model extracts explicit symptom evidence from free-form patient text.
    It DOES NOT diagnose, prescribe, or assign urgency levels.
    """

    findings: list[AITriageFindingItem] = Field(default_factory=list)
    summary_notes: str | None = None

    model_config = ConfigDict(extra="ignore")
