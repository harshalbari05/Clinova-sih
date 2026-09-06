"""Clinical Summary & Physician Review Endpoints.

Routes:
- POST /api/v1/consultations/{consultation_id}/summary/generate
- GET  /api/v1/consultations/{consultation_id}/summary
- PUT  /api/v1/consultations/{consultation_id}/summary
- POST /api/v1/consultations/{consultation_id}/summary/confirm
- POST /api/v1/consultations/{consultation_id}/summary/reject
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Body, status

from app.api.deps import CurrentUserDep, DatabaseDep
from app.schemas.summary import (
    SummaryConfirmRequest,
    SummaryEditRequest,
    SummaryGenerateRequest,
    SummaryRejectRequest,
    SummaryResponse,
)
from app.summary.service import clinical_summary_service

router = APIRouter()


@router.post(
    "/consultations/{consultation_id}/summary/generate",
    response_model=SummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate AI Clinical Summary Draft",
    description="Generate or regenerate an objective, non-diagnostic pre-consultation clinical summary draft.",
)
async def generate_summary(
    consultation_id: uuid.UUID,
    user: CurrentUserDep,
    db: DatabaseDep,
    payload: SummaryGenerateRequest = Body(default_factory=SummaryGenerateRequest),
) -> SummaryResponse:
    """Generate or retrieve a pre-consultation draft summary."""
    summary = await clinical_summary_service.get_or_generate_summary(
        db=db,
        consultation_id=consultation_id,
        user=user,
        force_rebuild=payload.force_rebuild,
    )
    return SummaryResponse.model_validate(summary)


@router.get(
    "/consultations/{consultation_id}/summary",
    response_model=SummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Clinical Summary",
    description="Retrieve the latest clinical summary for a consultation (auto-generating draft if none exists).",
)
async def get_summary(
    consultation_id: uuid.UUID,
    user: CurrentUserDep,
    db: DatabaseDep,
) -> SummaryResponse:
    """Get the current clinical summary for a consultation."""
    summary = await clinical_summary_service.get_summary(
        db=db,
        consultation_id=consultation_id,
        user=user,
    )
    return SummaryResponse.model_validate(summary)


@router.put(
    "/consultations/{consultation_id}/summary",
    response_model=SummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Edit Clinical Summary Draft (Clinician Only)",
    description="Allow an authorized hospital clinician to edit the narrative, structured data, and add notes.",
)
async def edit_summary(
    consultation_id: uuid.UUID,
    user: CurrentUserDep,
    db: DatabaseDep,
    payload: SummaryEditRequest,
) -> SummaryResponse:
    """Clinician edits to an existing summary draft."""
    summary = await clinical_summary_service.edit_summary(
        db=db,
        consultation_id=consultation_id,
        user=user,
        payload=payload,
    )
    return SummaryResponse.model_validate(summary)


@router.post(
    "/consultations/{consultation_id}/summary/confirm",
    response_model=SummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm & Finalize Clinical Summary (Clinician Only)",
    description="Physician confirms and finalizes the summary, advancing consultation status to 'reviewed'.",
)
async def confirm_summary(
    consultation_id: uuid.UUID,
    user: CurrentUserDep,
    db: DatabaseDep,
    payload: SummaryConfirmRequest = Body(default_factory=SummaryConfirmRequest),
) -> SummaryResponse:
    """Physician finalization and sign-off on summary."""
    summary = await clinical_summary_service.confirm_summary(
        db=db,
        consultation_id=consultation_id,
        user=user,
        payload=payload,
    )
    return SummaryResponse.model_validate(summary)


@router.post(
    "/consultations/{consultation_id}/summary/reject",
    response_model=SummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject Clinical Summary Draft (Clinician Only)",
    description="Physician rejects/discards the AI summary draft with a stated clinical reason.",
)
async def reject_summary(
    consultation_id: uuid.UUID,
    user: CurrentUserDep,
    db: DatabaseDep,
    payload: SummaryRejectRequest,
) -> SummaryResponse:
    """Physician rejection of draft summary."""
    summary = await clinical_summary_service.reject_summary(
        db=db,
        consultation_id=consultation_id,
        user=user,
        payload=payload,
    )
    return SummaryResponse.model_validate(summary)
