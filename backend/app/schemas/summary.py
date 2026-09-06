"""Pydantic schemas for Step 9: AI Clinical Summary & Physician Review."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SummaryStatus(str, enum.Enum):
    """Lifecycle status of a clinical summary."""

    DRAFT = "draft"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class SummarySourceType(str, enum.Enum):
    """Source attribution for information in the clinical summary."""

    PATIENT_REPORTED = "PATIENT_REPORTED"
    DOCUMENT_EXTRACTED = "DOCUMENT_EXTRACTED"
    CLINICAL_HISTORY = "CLINICAL_HISTORY"
    TRIAGE_ALERT = "TRIAGE_ALERT"
    CLINICIAN_ENTERED = "CLINICIAN_ENTERED"


class ProvenanceItem(BaseModel):
    """Clinical finding with source attribution and verbatim evidence."""

    item: str = Field(..., description="The clinical fact or observation.")
    source_type: str = Field(
        SummarySourceType.PATIENT_REPORTED.value,
        description="Source type (PATIENT_REPORTED, DOCUMENT_EXTRACTED, CLINICAL_HISTORY, TRIAGE_ALERT, CLINICIAN_ENTERED).",
    )
    source_id: str | None = Field(
        None, description="UUID or identifier of the source record."
    )
    evidence: str | None = Field(
        None, description="Verbatim quote or excerpt from the source."
    )


class SummaryMedication(BaseModel):
    """Medication item in the summary."""

    name: str = Field(..., description="Name of medication.")
    dosage: str | None = Field(None, description="Dosage and strength.")
    frequency: str | None = Field(None, description="Frequency and schedule.")
    source_type: str = Field(
        SummarySourceType.PATIENT_REPORTED.value,
        description="Attribution source.",
    )
    evidence: str | None = Field(None, description="Verbatim evidence text.")


class SummaryAllergy(BaseModel):
    """Allergy item in the summary."""

    allergen: str = Field(..., description="Substance or allergen.")
    reaction: str | None = Field(None, description="Documented reaction.")
    severity: str | None = Field(None, description="Severity (mild, moderate, severe).")
    source_type: str = Field(
        SummarySourceType.PATIENT_REPORTED.value,
        description="Attribution source.",
    )


class SummaryInvestigation(BaseModel):
    """Laboratory test or investigation finding."""

    test_name: str = Field(..., description="Name of laboratory test or investigation.")
    result_value: str = Field(..., description="Measured result.")
    unit: str | None = Field(None, description="Measurement unit.")
    reference_range: str | None = Field(None, description="Normal reference range.")
    flag: str | None = Field(None, description="Abnormality flag (high, low, abnormal, normal).")
    source_document: str | None = Field(None, description="Title/filename of source document.")
    evidence: str | None = Field(None, description="Verbatim excerpt from report.")


class SummaryTriageAlert(BaseModel):
    """Red flag or triage finding."""

    alert_type: str = Field(..., description="Type or category of red flag.")
    severity: str = Field(..., description="Severity level (low, medium, high, critical).")
    message: str = Field(..., description="Description of the finding.")
    status: str = Field("active", description="Status of the alert.")


class SummaryTimelineEvent(BaseModel):
    """Chronological event highlight in the summary."""

    event_date: str | None = Field(None, description="Date or timeframe of the event.")
    event_type: str = Field(..., description="Type of event.")
    title: str = Field(..., description="Short title of the event.")
    verification_status: str = Field("UNVERIFIED", description="Verification status.")


class StructuredSummary(BaseModel):
    """Structured JSON representation of the clinical summary."""

    chief_complaint: str | None = Field(None, description="Primary reason for consultation.")
    history_of_present_illness: str | None = Field(
        None, description="Chronological narrative of present illness."
    )
    patient_reported_symptoms: list[ProvenanceItem] = Field(
        default_factory=list, description="Symptoms reported directly by the patient."
    )
    past_medical_history: list[ProvenanceItem] = Field(
        default_factory=list, description="Documented or reported medical conditions."
    )
    past_surgical_history: list[ProvenanceItem] = Field(
        default_factory=list, description="Past surgeries and procedures."
    )
    current_medications: list[SummaryMedication] = Field(
        default_factory=list, description="Current or active medications."
    )
    allergies: list[SummaryAllergy] = Field(
        default_factory=list, description="Documented or reported allergies."
    )
    family_and_social_history: list[ProvenanceItem] = Field(
        default_factory=list, description="Relevant family and social background."
    )
    relevant_investigations: list[SummaryInvestigation] = Field(
        default_factory=list, description="Key laboratory and diagnostic investigation findings."
    )
    triage_and_red_flags: list[SummaryTriageAlert] = Field(
        default_factory=list, description="Active red flags and triage alerts."
    )
    timeline_highlights: list[SummaryTimelineEvent] = Field(
        default_factory=list, description="Key chronological milestones from medical timeline."
    )
    unreported_or_unclear_areas: list[str] = Field(
        default_factory=list, description="Important history categories with missing or ambiguous data."
    )
    clinician_notes: str | None = Field(
        None, description="Notes and commentary entered by the reviewing clinician."
    )
    disclaimer: str = Field(
        "AI-generated clinical draft for physician review only. Not a medical diagnosis or treatment plan.",
        description="Mandatory clinical safety disclaimer.",
    )


# ---------------------------------------------------------------------------
# Request & Response Models
# ---------------------------------------------------------------------------


class SummaryGenerateRequest(BaseModel):
    """Payload to trigger or force-rebuild an AI summary draft."""

    force_rebuild: bool = Field(
        False,
        description="If True, discards existing unconfirmed draft and generates a new draft.",
    )


class SummaryEditRequest(BaseModel):
    """Payload for clinician editing an existing draft summary."""

    summary_text: str | None = Field(
        None, description="Updated summary narrative text."
    )
    structured_summary: dict[str, Any] | None = Field(
        None, description="Updated structured JSON summary."
    )
    clinician_notes: str | None = Field(
        None, description="Clinician observations, addenda, or edits."
    )


class SummaryConfirmRequest(BaseModel):
    """Payload for physician finalization/confirmation of summary."""

    clinician_notes: str | None = Field(
        None, description="Optional final notes before confirmation."
    )
    confirm_timeline_events: bool = Field(
        True,
        description="If True, upgrades unverified/source-confirmed timeline events for this consultation to CLINICIAN_VERIFIED.",
    )


class SummaryRejectRequest(BaseModel):
    """Payload for clinician discarding/rejecting the AI draft."""

    reason: str = Field(
        ...,
        min_length=3,
        description="Clinician's stated clinical rationale for rejecting the draft.",
    )


class SummaryResponse(BaseModel):
    """Response model representing a clinical summary."""

    id: uuid.UUID
    consultation_id: uuid.UUID
    summary_text: str
    structured_summary: dict[str, Any] | None = None
    ai_draft_text: str | None = None
    generated_by: str
    version: int
    status: str
    reviewed_by_id: uuid.UUID | None = None
    reviewed_at: datetime | None = None
    clinician_notes: str | None = None
    rejection_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
