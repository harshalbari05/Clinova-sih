"""Medical Timeline API endpoints.

Routes:
- GET  /api/v1/patients/me/timeline
- POST /api/v1/patients/me/timeline/rebuild
- GET  /api/v1/patients/{patient_id}/timeline
- GET  /api/v1/consultations/{consultation_id}/timeline
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import CurrentPatientDep, CurrentUserDep, DatabaseDep
from app.schemas.timeline import (
    PatientTimelineResponse,
    TimelineEventResponse,
    TimelineFilterParams,
)
from app.timeline.service import timeline_service

router = APIRouter()


@router.get(
    "/patients/me/timeline",
    response_model=PatientTimelineResponse,
    status_code=status.HTTP_200_OK,
    summary="Get My Medical Timeline",
    description="Retrieve the authenticated patient's structured chronological medical timeline.",
)
async def get_my_timeline(
    current_patient: CurrentPatientDep,
    db: DatabaseDep,
    event_type: str | None = Query(None, description="Filter by event type"),
    source_type: str | None = Query(None, description="Filter by source type"),
    start_date: date | None = Query(None, description="Filter events on or after date"),
    end_date: date | None = Query(None, description="Filter events on or before date"),
    order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order: asc or desc"),
) -> PatientTimelineResponse:
    """Retrieve the authenticated patient's chronological timeline."""
    _user, patient = current_patient
    filters = TimelineFilterParams(
        event_type=event_type,
        source_type=source_type,
        start_date=start_date,
        end_date=end_date,
        order=order,
    )
    events = await timeline_service.get_patient_timeline(db, patient.id, filters)
    return PatientTimelineResponse(
        patient_id=patient.id,
        total_events=len(events),
        events=[TimelineEventResponse.model_validate(e) for e in events],
        generated_at=datetime.now(timezone.utc),
    )


@router.post(
    "/patients/me/timeline/rebuild",
    response_model=PatientTimelineResponse,
    status_code=status.HTTP_200_OK,
    summary="Rebuild My Medical Timeline",
    description="Idempotently re-extract and synchronize all timeline events for the authenticated patient.",
)
async def rebuild_my_timeline(
    current_patient: CurrentPatientDep,
    db: DatabaseDep,
) -> PatientTimelineResponse:
    """Trigger an idempotent full rebuild of the authenticated patient's timeline."""
    _user, patient = current_patient
    events = await timeline_service.build_patient_timeline(db, patient.id)
    return PatientTimelineResponse(
        patient_id=patient.id,
        total_events=len(events),
        events=[TimelineEventResponse.model_validate(e) for e in events],
        generated_at=datetime.now(timezone.utc),
    )


@router.get(
    "/consultations/{consultation_id}/timeline",
    response_model=PatientTimelineResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Consultation Patient Timeline",
    description="Retrieve the patient's medical timeline scoped by consultation access authorization.",
)
async def get_consultation_timeline(
    consultation_id: uuid.UUID,
    user: CurrentUserDep,
    db: DatabaseDep,
    event_type: str | None = Query(None, description="Filter by event type"),
    source_type: str | None = Query(None, description="Filter by source type"),
    start_date: date | None = Query(None, description="Filter events on or after date"),
    end_date: date | None = Query(None, description="Filter events on or before date"),
    order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order: asc or desc"),
) -> PatientTimelineResponse:
    """Authorized endpoint for patient or hospital staff to view timeline in consultation context."""
    consultation = await timeline_service.authorize_consultation_timeline_access(
        db, user, consultation_id
    )
    filters = TimelineFilterParams(
        event_type=event_type,
        source_type=source_type,
        start_date=start_date,
        end_date=end_date,
        order=order,
    )
    events = await timeline_service.get_patient_timeline(
        db, consultation.patient_id, filters
    )
    return PatientTimelineResponse(
        patient_id=consultation.patient_id,
        total_events=len(events),
        events=[TimelineEventResponse.model_validate(e) for e in events],
        generated_at=datetime.now(timezone.utc),
    )


@router.get(
    "/patients/{patient_id}/timeline",
    response_model=PatientTimelineResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Patient Timeline by ID",
    description="Retrieve patient timeline by patient ID with facility-level authorization.",
)
async def get_patient_timeline_by_id(
    patient_id: uuid.UUID,
    user: CurrentUserDep,
    db: DatabaseDep,
    event_type: str | None = Query(None, description="Filter by event type"),
    source_type: str | None = Query(None, description="Filter by source type"),
    start_date: date | None = Query(None, description="Filter events on or after date"),
    end_date: date | None = Query(None, description="Filter events on or before date"),
    order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order: asc or desc"),
) -> PatientTimelineResponse:
    """Authorized endpoint for hospital staff or owning patient to retrieve patient timeline."""
    patient = await timeline_service.authorize_patient_timeline_access(
        db, user, patient_id
    )
    filters = TimelineFilterParams(
        event_type=event_type,
        source_type=source_type,
        start_date=start_date,
        end_date=end_date,
        order=order,
    )
    events = await timeline_service.get_patient_timeline(db, patient.id, filters)
    return PatientTimelineResponse(
        patient_id=patient.id,
        total_events=len(events),
        events=[TimelineEventResponse.model_validate(e) for e in events],
        generated_at=datetime.now(timezone.utc),
    )
