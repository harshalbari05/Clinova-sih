"""Pydantic schemas for medical document upload, OCR, and structured extraction.

Strict non-diagnostic design:
- Fields represent ONLY what is explicitly documented in the source document.
- Evidence and source page references are preserved for physician verification.
- Low-confidence or unreadable text is marked as uncertain.
"""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DocumentType(str, enum.Enum):
    """Controlled set of medical document types supported by Clinova."""

    PRESCRIPTION = "prescription"
    LAB_REPORT = "lab_report"
    DISCHARGE_SUMMARY = "discharge_summary"
    DIAGNOSTIC_REPORT = "diagnostic_report"
    CONSULTATION_NOTE = "consultation_note"
    MEDICAL_CERTIFICATE = "medical_certificate"
    OTHER = "other"

    @classmethod
    def from_string(cls, value: str | None) -> DocumentType:
        """Parse case-insensitively or return OTHER."""
        if not value:
            return cls.OTHER
        clean = value.strip().lower().replace(" ", "_").replace("-", "_")
        for member in cls:
            if member.value == clean or member.name.lower() == clean:
                return member
        return cls.OTHER


class ProcessingStatus(str, enum.Enum):
    """Consolidated processing status across OCR and AI extraction."""

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    OCR_COMPLETED = "ocr_completed"
    EXTRACTION_COMPLETED = "extraction_completed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Structured Extraction Schemas (Evidence-Based & Non-Diagnostic)
# ---------------------------------------------------------------------------


class MedicationExtraction(BaseModel):
    """Structured representation of a medication documented in the record."""

    name_as_written: str = Field(
        ...,
        description="Medication name exactly as written in the source document.",
    )
    dose_as_written: str | None = Field(
        default=None,
        description="Dosage as written (e.g. '500mg', '1 tablet').",
    )
    frequency_as_written: str | None = Field(
        default=None,
        description="Frequency as written (e.g. 'once daily', 'TDS', 'BD').",
    )
    route_as_written: str | None = Field(
        default=None,
        description="Route as written (e.g. 'oral', 'IV', 'topical').",
    )
    duration_as_written: str | None = Field(
        default=None,
        description="Duration as written (e.g. '5 days', '1 month').",
    )
    instructions_as_written: str | None = Field(
        default=None,
        description="Special instructions as written (e.g. 'after food').",
    )
    source_page: int | None = Field(
        default=None,
        description="Page number in source document where medication appears.",
    )
    evidence: str = Field(
        default="",
        description="Exact snippet or quote from OCR text serving as evidence.",
    )
    is_uncertain: bool = Field(
        default=False,
        description="True if the text was handwritten, blurry, or ambiguous.",
    )


class LabResultExtraction(BaseModel):
    """Structured representation of a laboratory investigation result."""

    test_name: str = Field(
        ...,
        description="Test name as written (e.g. 'Hemoglobin', 'Serum Creatinine').",
    )
    value: str = Field(
        ...,
        description="Result value as written (e.g. '13.5', 'Negative').",
    )
    unit: str | None = Field(
        default=None,
        description="Measurement unit (e.g. 'g/dL', 'mg/dL').",
    )
    reference_range: str | None = Field(
        default=None,
        description="Documented biological reference interval if present.",
    )
    abnormal_flag_as_documented: str | None = Field(
        default=None,
        description="Documented abnormal flag (e.g. 'HIGH', 'LOW', 'H', 'L').",
    )
    test_date: str | None = Field(
        default=None,
        description="Date of specimen collection or test completion if documented.",
    )
    source_page: int | None = Field(
        default=None,
        description="Source page number.",
    )
    evidence: str = Field(
        default="",
        description="Exact snippet from source document for verification.",
    )


class DocumentExtraction(BaseModel):
    """Complete structured extraction from a medical document.

    STRICT MEDICAL SAFETY RULES:
    - Never diagnose illnesses or deduce conclusions not stated in the document.
    - If a field was not explicitly written, keep it null or empty.
    - Preserve evidence and source page for all clinical statements.
    """

    document_type: str | None = Field(
        None,
        description="Inferred or verified document classification.",
    )
    document_date: str | None = Field(
        None,
        description="Primary date of the document (e.g. report date, prescription date).",
    )
    hospital_or_clinic_name: str | None = Field(
        None,
        description="Name of the healthcare facility as written.",
    )
    doctor_name: str | None = Field(
        None,
        description="Name of the prescribing/reporting physician as written.",
    )
    patient_name_as_written: str | None = Field(
        None,
        description="Patient name as documented.",
    )
    patient_identifier_as_written: str | None = Field(
        None,
        description="MRN, UHID, or registration number as documented.",
    )
    diagnoses_or_conditions_as_documented: list[str] = Field(
        default_factory=list,
        description="Diagnoses or medical impressions explicitly documented by the doctor.",
    )
    symptoms_as_documented: list[str] = Field(
        default_factory=list,
        description="Patient symptoms or complaints explicitly recorded in the document.",
    )
    medications: list[MedicationExtraction] = Field(
        default_factory=list,
        description="List of prescribed or administered medications.",
    )
    allergies: list[str] = Field(
        default_factory=list,
        description="Documented drug or substance allergies.",
    )
    investigations: list[str] = Field(
        default_factory=list,
        description="Diagnostic tests ordered or performed (e.g. 'ECG', 'Chest X-Ray').",
    )
    laboratory_results: list[LabResultExtraction] = Field(
        default_factory=list,
        description="Documented laboratory measurements.",
    )
    imaging_findings: list[str] = Field(
        default_factory=list,
        description="Radiological or imaging impressions explicitly documented.",
    )
    procedures: list[str] = Field(
        default_factory=list,
        description="Procedures or surgeries explicitly documented.",
    )
    admission_date: str | None = Field(
        None,
        description="Hospital admission date if applicable.",
    )
    discharge_date: str | None = Field(
        None,
        description="Hospital discharge date if applicable.",
    )
    follow_up_instructions_as_documented: str | None = Field(
        None,
        description="Follow-up instructions or advice explicitly given in the document.",
    )
    other_clinical_information: list[str] = Field(
        default_factory=list,
        description="Any other noteworthy clinical observations explicitly stated.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Warnings regarding OCR quality, ambiguity, or missing pages.",
    )
    confidence_score: float | None = Field(
        None,
        description="Optional model-assigned confidence score between 0.0 and 1.0.",
    )


# ---------------------------------------------------------------------------
# API Responses
# ---------------------------------------------------------------------------


class MedicalDocumentResponse(BaseModel):
    """Metadata response for a medical document."""

    id: uuid.UUID
    patient_id: uuid.UUID
    consultation_id: uuid.UUID | None = None
    file_name: str
    document_type: str
    document_date: date | None = None
    mime_type: str | None = None
    ocr_status: str
    processing_status: str
    uploaded_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MedicalDocumentListResponse(BaseModel):
    """Paginated list of medical documents."""

    items: list[MedicalDocumentResponse]
    total: int
    limit: int
    offset: int


class ExtractedDataResponse(BaseModel):
    """Structured extraction response for a document."""

    document_id: uuid.UUID
    ocr_status: str
    extraction_status: str
    raw_ocr_text: str | None = None
    extracted_data: DocumentExtraction | None = None
    extracted_at: datetime | None = None
    warnings: list[str] = Field(default_factory=list)
