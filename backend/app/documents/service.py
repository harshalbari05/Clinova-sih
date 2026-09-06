"""Medical document business service.

Coordinates:
- Secure file upload validation (extensions, MIME, magic bytes, file size).
- Storage via StorageProvider.
- Consultation ownership validation.
- OCR text extraction & AI structured clinical extraction.
- Database persistence across MedicalDocument and ExtractedData.
- Audit logging of upload and access events.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.documents.extraction import document_extraction_service
from app.documents.ocr.base import OCRError, OCRResult
from app.documents.processor import document_processor
from app.documents.schemas import (
    DocumentExtraction,
    DocumentType,
    ExtractedDataResponse,
    MedicalDocumentListResponse,
    MedicalDocumentResponse,
    ProcessingStatus,
)
from app.documents.storage import StorageError, storage_provider
from app.models.audit_log import AuditLog
from app.models.consultation import Consultation
from app.models.extracted_data import ExtractedData
from app.models.hospital_user import HospitalUser
from app.models.medical_document import MedicalDocument
from app.models.patient import Patient
from app.models.user import User

logger = logging.getLogger(__name__)

# Allowed MIME types and extensions
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}

ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def _detect_mime_from_magic_bytes(content: bytes) -> str | None:
    """Validate content binary signature (magic bytes) to prevent file-type spoofing."""
    if len(content) < 4:
        return None

    # PDF: %PDF-
    if content.startswith(b"%PDF-"):
        return "application/pdf"

    # JPEG: \xff\xd8\xff
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"

    # PNG: \x89PNG\r\n\x1a\n
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"

    # WEBP: starts with RIFF and has WEBP at offset 8
    if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp"

    return None


class MedicalDocumentService:
    """Service handling medical document lifecycle and structured processing."""

    def validate_file(
        self,
        content: bytes,
        filename: str,
        declared_mime_type: str | None = None,
    ) -> str:
        """Perform strict security validation on uploaded file bytes."""
        # 1. Check file size
        max_bytes = settings.MEDICAL_DOCUMENT_MAX_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413),
                detail=f"File exceeds maximum allowed size of {settings.MEDICAL_DOCUMENT_MAX_SIZE_MB}MB.",
            )

        # 2. Check non-empty
        if len(content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )

        # 3. Check extension
        _, ext = os.path.splitext(filename.lower())
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file extension '{ext}'. Allowed formats: PDF, JPEG, PNG, WEBP.",
            )

        # 4. Check magic bytes
        detected_mime = _detect_mime_from_magic_bytes(content)
        if detected_mime is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content does not match a supported binary format or is corrupted.",
            )

        # Validate extension matches magic bytes
        if detected_mime == "application/pdf" and ext != ".pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File header indicates PDF, but file extension does not match.",
            )
        if detected_mime == "image/jpeg" and ext not in (".jpg", ".jpeg"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File header indicates JPEG, but file extension does not match.",
            )
        if detected_mime == "image/png" and ext != ".png":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File header indicates PNG, but file extension does not match.",
            )
        if detected_mime == "image/webp" and ext != ".webp":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File header indicates WEBP, but file extension does not match.",
            )

        return detected_mime

    def _sanitize_filename(self, raw_filename: str) -> str:
        """Sanitize filename to prevent directory traversal and special chars."""
        base = os.path.basename(raw_filename).strip()
        # Remove null bytes or path separators
        clean = base.replace("\0", "").replace("/", "").replace("\\", "")
        return clean or "document"

    def _compute_processing_status(
        self,
        ocr_status: str,
        extracted_data: ExtractedData | None,
    ) -> str:
        """Derive consolidated user-facing processing status."""
        if ocr_status == "failed":
            return ProcessingStatus.FAILED.value
        if ocr_status == "processing":
            return ProcessingStatus.PROCESSING.value

        if extracted_data is not None:
            if extracted_data.extraction_status == "completed":
                return ProcessingStatus.EXTRACTION_COMPLETED.value
            if extracted_data.extraction_status == "failed":
                return ProcessingStatus.OCR_COMPLETED.value
            if extracted_data.extraction_status == "processing":
                return ProcessingStatus.PROCESSING.value

        if ocr_status == "completed":
            return ProcessingStatus.OCR_COMPLETED.value

        return ProcessingStatus.UPLOADED.value

    def to_response(
        self,
        doc: MedicalDocument,
        extracted: ExtractedData | None = None,
    ) -> MedicalDocumentResponse:
        """Convert a MedicalDocument model to its API response schema."""
        ext = extracted
        if ext is None and "extracted_data" in doc.__dict__:
            ext = doc.__dict__["extracted_data"]
        status_val = self._compute_processing_status(doc.ocr_status, ext)
        return MedicalDocumentResponse(
            id=doc.id,
            patient_id=doc.patient_id,
            consultation_id=doc.consultation_id,
            file_name=doc.file_name,
            document_type=doc.document_type,
            document_date=doc.document_date,
            mime_type=doc.mime_type,
            ocr_status=doc.ocr_status,
            processing_status=status_val,
            uploaded_at=doc.uploaded_at,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )

    async def _audit(
        self,
        db: AsyncSession,
        user_id: uuid.UUID | None,
        action: str,
        doc_id: uuid.UUID,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record an audit trail event without leaking sensitive clinical text."""
        audit_entry = AuditLog(
            id=uuid.uuid4(),
            user_id=user_id,
            action=action,
            entity_type="medical_document",
            entity_id=str(doc_id),
            metadata_json=metadata or {},
        )
        db.add(audit_entry)

    async def upload_document(
        self,
        db: AsyncSession,
        patient: Patient,
        file_content: bytes,
        original_filename: str,
        document_type_str: str | None = None,
        consultation_id: uuid.UUID | None = None,
        document_date: date | None = None,
        declared_mime_type: str | None = None,
        process_immediately: bool = True,
    ) -> MedicalDocumentResponse:
        """Upload, validate, store, and optionally process a medical document."""
        # 1. If consultation_id provided, verify patient owns it
        if consultation_id is not None:
            stmt = select(Consultation).where(Consultation.id == consultation_id)
            consultation = (await db.execute(stmt)).scalar_one_or_none()
            if consultation is None or consultation.patient_id != patient.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Consultation not found.",
                )

        # 2. Validate file bytes and detect canonical MIME
        safe_filename = self._sanitize_filename(original_filename)
        canonical_mime = self.validate_file(
            file_content,
            safe_filename,
            declared_mime_type,
        )

        # 3. Store raw binary file via StorageProvider
        try:
            storage_identifier, _ = await storage_provider.save_file(
                content=file_content,
                original_filename=safe_filename,
                patient_id=patient.id,
            )
        except StorageError as exc:
            logger.error("Failed to store medical document: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to persist uploaded document safely.",
            ) from exc

        # 4. Resolve document type enum
        doc_type = DocumentType.from_string(document_type_str)

        # 5. Create database record
        doc = MedicalDocument(
            id=uuid.uuid4(),
            patient_id=patient.id,
            consultation_id=consultation_id,
            file_name=safe_filename,
            file_url=storage_identifier,
            document_type=doc_type.value,
            document_date=document_date,
            mime_type=canonical_mime,
            ocr_status="pending",
        )
        db.add(doc)
        await db.flush()

        # 6. Audit upload event
        await self._audit(
            db,
            user_id=patient.user_id,
            action="document_uploaded",
            doc_id=doc.id,
            metadata={
                "document_type": doc_type.value,
                "file_name": safe_filename,
                "mime_type": canonical_mime,
                "consultation_id": str(consultation_id) if consultation_id else None,
            },
        )

        # 7. Immediate processing if requested & enabled
        extracted_row: ExtractedData | None = None
        if process_immediately and settings.DOCUMENT_PROCESSING_ENABLED:
            extracted_row = await self.process_document(db, doc)

        await db.commit()
        await db.refresh(doc)

        return self.to_response(doc, extracted_row)

    async def process_document(
        self,
        db: AsyncSession,
        doc: MedicalDocument,
    ) -> ExtractedData:
        """Execute OCR extraction and structured AI extraction on a stored document."""
        doc.ocr_status = "processing"
        await db.flush()

        # 1. Resolve local path to stored document
        try:
            file_path = storage_provider.get_file_path(doc.file_url)
        except Exception as exc:
            logger.error("Stored document file not accessible for doc %s: %s", doc.id, exc)
            doc.ocr_status = "failed"
            await db.flush()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Document file could not be accessed from storage.",
            ) from exc

        # 2. Query or create ExtractedData record
        stmt = select(ExtractedData).where(ExtractedData.document_id == doc.id)
        extracted = (await db.execute(stmt)).scalar_one_or_none()
        if extracted is None:
            extracted = ExtractedData(
                id=uuid.uuid4(),
                document_id=doc.id,
                extraction_status="processing",
            )
            db.add(extracted)
        else:
            extracted.extraction_status = "processing"
        await db.flush()

        # 3. Perform OCR / Text extraction
        ocr_result: OCRResult | None = None
        try:
            ocr_result = await document_processor.extract_document_text(
                file_path=file_path,
                mime_type=doc.mime_type or "application/octet-stream",
            )
            doc.ocr_status = "completed"
            extracted.raw_ocr_text = ocr_result.text
        except OCRError as ocr_err:
            logger.warning(
                "OCR processing failed for doc %s (%s): %s",
                doc.id,
                ocr_err.category,
                ocr_err.message,
            )
            doc.ocr_status = "failed"
            extracted.extraction_status = "failed"
            extracted.extracted_json = {
                "warnings": [f"OCR error ({ocr_err.category}): {ocr_err.message}"]
            }
            await db.flush()
            return extracted
        except Exception as exc:
            logger.warning("Unexpected error during OCR for doc %s: %s", doc.id, exc)
            doc.ocr_status = "failed"
            extracted.extraction_status = "failed"
            extracted.extracted_json = {"warnings": [f"OCR processing failed: {exc}"]}
            await db.flush()
            return extracted

        # 4. Perform AI Structured Extraction
        extraction_data, extraction_warnings = await document_extraction_service.extract_structured_data(
            ocr_result=ocr_result,
            claimed_type=doc.document_type,
            document_date_hint=str(doc.document_date) if doc.document_date else None,
        )

        if extraction_data is not None:
            extracted.extracted_json = extraction_data.model_dump()
            extracted.extraction_status = "completed"
            extracted.extracted_at = datetime.now(timezone.utc)
        else:
            extracted.extraction_status = "failed"
            extracted.extracted_json = {"warnings": extraction_warnings}

        await db.flush()
        return extracted

    async def authorize_document_access(
        self,
        db: AsyncSession,
        user: User,
        document_id: uuid.UUID,
    ) -> MedicalDocument:
        """Ensure caller is either the owning patient or an authorized hospital user.

        Raises:
            HTTPException(404): If document not found or owned by another patient.
            HTTPException(403): If user has no valid clinical role.
        """
        stmt = (
            select(MedicalDocument)
            .options(selectinload(MedicalDocument.extracted_data))
            .where(MedicalDocument.id == document_id)
        )
        doc = (await db.execute(stmt)).scalar_one_or_none()

        if doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medical document not found.",
            )

        # Check Patient ownership
        p_stmt = select(Patient).where(Patient.user_id == user.id)
        patient = (await db.execute(p_stmt)).scalar_one_or_none()

        if patient is not None:
            if doc.patient_id != patient.id:
                # Safe 404: Do not leak existence of other patients' documents
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Medical document not found.",
                )
            return doc

        # Check Hospital staff authorization
        h_stmt = select(HospitalUser).where(HospitalUser.user_id == user.id)
        h_user = (await db.execute(h_stmt)).scalar_one_or_none()

        if h_user is not None:
            # If doc is attached to a consultation, must match hospital facility
            if doc.consultation_id is not None:
                c_stmt = select(Consultation).where(Consultation.id == doc.consultation_id)
                consultation = (await db.execute(c_stmt)).scalar_one_or_none()
                if consultation is not None and consultation.hospital_id == h_user.hospital_id:
                    return doc

            # Alternatively, if patient has an active consultation with this hospital
            patient_consultations_stmt = select(Consultation).where(
                Consultation.patient_id == doc.patient_id,
                Consultation.hospital_id == h_user.hospital_id,
            )
            has_facility_relation = (
                await db.execute(patient_consultations_stmt)
            ).scalars().first()

            if has_facility_relation is not None:
                return doc

            # Unauthorized hospital access -> Safe 404
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medical document not found.",
            )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not authorized to access medical records.",
        )

    async def list_documents(
        self,
        db: AsyncSession,
        user: User,
        consultation_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> MedicalDocumentListResponse:
        """List medical documents belonging to the authenticated patient or hospital."""
        p_stmt = select(Patient).where(Patient.user_id == user.id)
        patient = (await db.execute(p_stmt)).scalar_one_or_none()

        if patient is not None:
            base_query = select(MedicalDocument).where(MedicalDocument.patient_id == patient.id)
            if consultation_id is not None:
                base_query = base_query.where(MedicalDocument.consultation_id == consultation_id)

            count_stmt = select(func.count()).select_from(base_query.subquery())
            total = (await db.execute(count_stmt)).scalar_one()

            query = (
                base_query.options(selectinload(MedicalDocument.extracted_data))
                .order_by(desc(MedicalDocument.uploaded_at))
                .limit(limit)
                .offset(offset)
            )
            docs = list((await db.execute(query)).scalars().all())

            items = [self.to_response(d) for d in docs]
            return MedicalDocumentListResponse(
                items=items,
                total=total,
                limit=limit,
                offset=offset,
            )

        # Check hospital user
        h_stmt = select(HospitalUser).where(HospitalUser.user_id == user.id)
        h_user = (await db.execute(h_stmt)).scalar_one_or_none()

        if h_user is not None:
            if consultation_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="consultation_id query parameter is required for hospital document listing.",
                )
            c_stmt = select(Consultation).where(Consultation.id == consultation_id)
            consultation = (await db.execute(c_stmt)).scalar_one_or_none()
            if consultation is None or consultation.hospital_id != h_user.hospital_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Consultation not found.",
                )

            base_query = select(MedicalDocument).where(
                MedicalDocument.consultation_id == consultation_id
            )
            count_stmt = select(func.count()).select_from(base_query.subquery())
            total = (await db.execute(count_stmt)).scalar_one()

            query = (
                base_query.options(selectinload(MedicalDocument.extracted_data))
                .order_by(desc(MedicalDocument.uploaded_at))
                .limit(limit)
                .offset(offset)
            )
            docs = list((await db.execute(query)).scalars().all())
            items = [self.to_response(d) for d in docs]
            return MedicalDocumentListResponse(
                items=items,
                total=total,
                limit=limit,
                offset=offset,
            )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not authorized to access medical records.",
        )

    async def get_document_file(
        self,
        db: AsyncSession,
        user: User,
        document_id: uuid.UUID,
    ) -> tuple[Path, str, str]:
        """Verify access and return (local_path, filename, mime_type) for download."""
        doc = await self.authorize_document_access(db, user, document_id)
        path = storage_provider.get_file_path(doc.file_url)

        await self._audit(
            db,
            user_id=user.id,
            action="document_downloaded",
            doc_id=doc.id,
            metadata={"file_name": doc.file_name},
        )
        await db.commit()

        return path, doc.file_name, doc.mime_type or "application/octet-stream"

    async def get_extraction(
        self,
        db: AsyncSession,
        user: User,
        document_id: uuid.UUID,
    ) -> ExtractedDataResponse:
        """Get structured extracted data for a document with verified access."""
        doc = await self.authorize_document_access(db, user, document_id)

        stmt = select(ExtractedData).where(ExtractedData.document_id == doc.id)
        extracted = (await db.execute(stmt)).scalar_one_or_none()

        parsed_extraction: DocumentExtraction | None = None
        warnings: list[str] = []

        if extracted is not None and extracted.extracted_json:
            try:
                parsed_extraction = DocumentExtraction.model_validate(extracted.extracted_json)
                if parsed_extraction.warnings:
                    warnings.extend(parsed_extraction.warnings)
            except Exception:
                # If extraction was not full DocumentExtraction (e.g. error payload)
                if "warnings" in extracted.extracted_json:
                    warnings.extend(extracted.extracted_json["warnings"])

        return ExtractedDataResponse(
            document_id=doc.id,
            ocr_status=doc.ocr_status,
            extraction_status=extracted.extraction_status if extracted else "pending",
            raw_ocr_text=extracted.raw_ocr_text if extracted else None,
            extracted_data=parsed_extraction,
            extracted_at=extracted.extracted_at if extracted else None,
            warnings=warnings,
        )


# Singleton instance
medical_document_service = MedicalDocumentService()
