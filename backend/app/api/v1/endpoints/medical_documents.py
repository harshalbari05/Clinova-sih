"""Medical Document API endpoints.

Routes:
    POST /api/v1/medical-documents                         — Upload a new medical document
    GET  /api/v1/medical-documents                         — List accessible documents
    GET  /api/v1/medical-documents/{document_id}           — Get metadata and processing status
    GET  /api/v1/medical-documents/{document_id}/file      — Download original binary file safely
    POST /api/v1/medical-documents/{document_id}/process   — Trigger or retry OCR & AI extraction
    GET  /api/v1/medical-documents/{document_id}/extraction — Retrieve structured extraction

Security:
    - Patients may only upload, list, download, and extract their own documents.
    - Cross-patient requests return safe 404 (preventing enumeration attacks).
    - Hospital staff may only access documents linked to consultations at their facility.
    - Path traversal is strictly defended at the storage provider layer.
"""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse

from app.api.deps import CurrentPatientDep, CurrentUserDep, DatabaseDep
from app.documents.schemas import (
    ExtractedDataResponse,
    MedicalDocumentListResponse,
    MedicalDocumentResponse,
)
from app.documents.service import medical_document_service

router = APIRouter()


@router.post(
    "",
    response_model=MedicalDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Medical Document",
    description=(
        "Upload a medical document (prescription, lab report, discharge summary, etc.). "
        "Supports PDF, JPEG, PNG, WEBP files up to 10MB. Performs secure magic-byte inspection, "
        "persists to storage abstraction, and triggers OCR + AI structured extraction."
    ),
)
async def upload_medical_document(
    current_patient: CurrentPatientDep,
    db: DatabaseDep,
    file: UploadFile = File(..., description="Document binary file (PDF, JPEG, PNG, WEBP)"),
    document_type: str = Form("other", description="Document type classification"),
    consultation_id: uuid.UUID | None = Form(None, description="Optional associated consultation ID"),
    document_date: date | None = Form(None, description="Optional primary document date"),
    process_immediately: bool = Form(True, description="Whether to run OCR & extraction immediately"),
) -> MedicalDocumentResponse:
    """Upload a medical document belonging to the authenticated patient."""
    _user, patient = current_patient

    try:
        content = await file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read uploaded file: {exc}",
        ) from exc

    return await medical_document_service.upload_document(
        db=db,
        patient=patient,
        file_content=content,
        original_filename=file.filename or "uploaded_document",
        document_type_str=document_type,
        consultation_id=consultation_id,
        document_date=document_date,
        declared_mime_type=file.content_type,
        process_immediately=process_immediately,
    )


@router.get(
    "",
    response_model=MedicalDocumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Medical Documents",
    description=(
        "List medical documents. For patients, returns their uploaded documents. "
        "For hospital staff, consultation_id is required to list documents for authorized consultations."
    ),
)
async def list_medical_documents(
    user: CurrentUserDep,
    db: DatabaseDep,
    consultation_id: uuid.UUID | None = Query(None, description="Optional consultation filter"),
    limit: int = Query(50, ge=1, le=100, description="Max items per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
) -> MedicalDocumentListResponse:
    """List documents for the authenticated caller."""
    return await medical_document_service.list_documents(
        db=db,
        user=user,
        consultation_id=consultation_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{document_id}",
    response_model=MedicalDocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Document Metadata",
    description="Retrieve metadata and processing status for a single medical document.",
)
async def get_medical_document(
    document_id: uuid.UUID,
    user: CurrentUserDep,
    db: DatabaseDep,
) -> MedicalDocumentResponse:
    """Get metadata for an authorized document."""
    doc = await medical_document_service.authorize_document_access(db, user, document_id)
    return medical_document_service.to_response(doc)


@router.get(
    "/{document_id}/file",
    response_class=FileResponse,
    status_code=status.HTTP_200_OK,
    summary="Download Original Document File",
    description="Securely download or view the original uploaded binary file.",
)
async def download_medical_document_file(
    document_id: uuid.UUID,
    user: CurrentUserDep,
    db: DatabaseDep,
) -> FileResponse:
    """Stream original document binary with verified authorization."""
    path, filename, mime_type = await medical_document_service.get_document_file(
        db=db,
        user=user,
        document_id=document_id,
    )
    return FileResponse(
        path=str(path),
        media_type=mime_type,
        filename=filename,
    )


@router.post(
    "/{document_id}/process",
    response_model=MedicalDocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger / Retry Document Processing",
    description="Trigger or retry OCR text extraction and AI structured clinical extraction.",
)
async def process_medical_document(
    document_id: uuid.UUID,
    user: CurrentUserDep,
    db: DatabaseDep,
) -> MedicalDocumentResponse:
    """Trigger or retry document processing."""
    doc = await medical_document_service.authorize_document_access(db, user, document_id)
    extracted = await medical_document_service.process_document(db, doc)
    await db.commit()
    await db.refresh(doc)
    return medical_document_service.to_response(doc, extracted)


@router.get(
    "/{document_id}/extraction",
    response_model=ExtractedDataResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Structured Extracted Data",
    description="Retrieve OCR text and evidence-backed structured clinical information.",
)
async def get_document_extraction(
    document_id: uuid.UUID,
    user: CurrentUserDep,
    db: DatabaseDep,
) -> ExtractedDataResponse:
    """Retrieve structured extraction results for an authorized document."""
    return await medical_document_service.get_extraction(
        db=db,
        user=user,
        document_id=document_id,
    )
