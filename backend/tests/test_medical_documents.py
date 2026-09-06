"""Comprehensive test suite for Clinova Step 7: Medical Document Processing, OCR & Structured Extraction.

Covers:
  Part 25 — File Security & Validation:
    1. Supported JPEG upload
    2. Supported PNG upload
    3. Supported PDF upload
    4. Unsupported extension rejected (400)
    5. Invalid MIME / magic-byte mismatch rejected (400)
    6. Empty file rejected (400)
    7. Oversized file rejected (413)
    8. Path traversal in filename sanitized
    9. Dangerous filename characters sanitized
    10. Duplicate filenames receive distinct safe storage keys
    11. Cross-patient document access blocked (safe 404)
    12. Unauthorized file download blocked (401/404)
    13. Patient can access and download own document
    14. Hospital user authorization enforced (404 for unauthorized facility)
    15. Invalid consultation association rejected (404)

  Part 26 — OCR Layer Tests:
    16. OCR success with mocked provider
    17. OCR empty text result handled with warning
    18. OCR provider failure handled (status 'failed', document preserved)
    19. OCR metadata preserved (character count, page count, etc.)
    20. Multi-page document handling
    21. Language configuration passed to provider
    22. Digital PDF embedded text extracted via pypdf
    23. Document processing retry endpoint (/process)

  Part 27 — AI Structured Extraction Tests:
    24. Valid structured clinical extraction into DocumentExtraction schema
    25. Missing optional fields defaulted to empty/null
    26. Malformed JSON handled gracefully without crashing
    27. Schema validation error handled gracefully
    28. AI provider error / timeout handled (OCR preserved, extraction 'failed')
    29. All AI providers unavailable fallback behavior
    30. Extraction contains source-supported fields only (non-diagnostic)
    31. Medication extraction with evidence and uncertainty flag
    32. Laboratory result extraction with values, units, and evidence

  Part 28 — End-to-End Integration Tests:
    33. End-to-end: Upload -> OCR -> AI structured extraction -> GET extraction
    34. OCR failure preserves original document and allows download
    35. AI failure preserves OCR text and document with safe pending/failed status
"""

from __future__ import annotations

import io
import json
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.registry import clear_provider_cache
from app.ai.router import task_router
from app.ai.schemas import AIErrorKind, AIProviderError, AIResponse
from app.ai.tasks import AITaskType
from app.documents.ocr.base import OCRError, OCRPageResult, OCRResult
from app.documents.processor import document_processor
from app.documents.schemas import DocumentExtraction, DocumentType, LabResultExtraction, MedicationExtraction
from app.documents.service import medical_document_service
from app.documents.storage import storage_provider
from app.models.consultation import Consultation
from app.models.extracted_data import ExtractedData
from app.models.hospital import Hospital
from app.models.hospital_user import HospitalUser
from app.models.medical_document import MedicalDocument
from app.models.patient import Patient
from app.models.user import User
from app.services.auth_service import create_access_token

# ---------------------------------------------------------------------------
# Test Helpers & Generators
# ---------------------------------------------------------------------------


def make_sample_image_bytes(fmt: str = "PNG", width: int = 100, height: int = 100) -> bytes:
    """Generate valid image binary bytes for testing."""
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def make_sample_pdf_bytes(text: str = "Clinova Test Medical Record - Paracetamol 500mg") -> bytes:
    """Generate minimal valid PDF binary with embedded text readable by pypdf."""
    stream_content = f"BT /F1 12 Tf 72 712 Td ({text}) Tj ET".encode("latin-1")
    length = len(stream_content)
    pdf = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
5 0 obj
<< /Length {length} >>
stream
{stream_content.decode('latin-1')}
endstream
endobj
xref
0 6
0000000000 65535 f 
0000000010 00000 n 
0000000060 00000 n 
0000000117 00000 n 
0000000227 00000 n 
0000000305 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
450
%%EOF
""".encode("latin-1")
    return pdf


async def _create_test_hospital(db: AsyncSession, name: str = "Apollo Hospital") -> Hospital:
    hospital = Hospital(
        id=uuid.uuid4(),
        name=name,
        registration_number=f"REG_{uuid.uuid4().hex[:6]}",
        address="456 Healthcare Rd",
        city="Pune",
        state="Maharashtra",
        pincode="411001",
        phone="+919876543210",
        email=f"hosp_{uuid.uuid4().hex[:6]}@example.com",
    )
    db.add(hospital)
    await db.commit()
    await db.refresh(hospital)
    return hospital


async def _create_patient_user(
    db: AsyncSession, email: str = "patient_doc@example.com"
) -> tuple[User, Patient, str]:
    user = User(
        id=uuid.uuid4(),
        email=email,
        phone=f"+91{uuid.uuid4().int % 10000000000:010d}",
        role="patient",
        is_active=True,
    )
    db.add(user)
    await db.flush()

    patient = Patient(
        id=uuid.uuid4(),
        user_id=user.id,
        full_name="Jane Doe",
    )
    db.add(patient)
    await db.commit()
    await db.refresh(user)
    await db.refresh(patient)

    token = create_access_token(
        data={"sub": str(user.id), "role": "patient", "user_type": "patient"}
    )
    return user, patient, token


async def _create_hospital_staff_user(
    db: AsyncSession, hospital_id: uuid.UUID, email: str = "doctor_doc@example.com"
) -> tuple[User, HospitalUser, str]:
    user = User(
        id=uuid.uuid4(),
        email=email,
        phone=f"+91{uuid.uuid4().int % 10000000000:010d}",
        role="hospital_staff",
        is_active=True,
    )
    db.add(user)
    await db.flush()

    h_user = HospitalUser(
        id=uuid.uuid4(),
        user_id=user.id,
        hospital_id=hospital_id,
        role="doctor",
    )
    db.add(h_user)
    await db.commit()
    await db.refresh(user)
    await db.refresh(h_user)

    token = create_access_token(
        data={"sub": str(user.id), "role": "hospital_staff", "user_type": "hospital_staff"}
    )
    return user, h_user, token


async def _create_consultation(
    db: AsyncSession, patient_id: uuid.UUID, hospital_id: uuid.UUID
) -> Consultation:
    consultation = Consultation(
        id=uuid.uuid4(),
        patient_id=patient_id,
        hospital_id=hospital_id,
        status="in_progress",
        chief_complaint="Fever and cough",
    )
    db.add(consultation)
    await db.commit()
    await db.refresh(consultation)
    return consultation


@pytest.fixture(autouse=True)
def reset_cache():
    clear_provider_cache()
    yield
    clear_provider_cache()


# ===========================================================================
# PART 25: FILE SECURITY & VALIDATION TESTS (1 - 15)
# ===========================================================================


@pytest.mark.asyncio
async def test_01_upload_supported_jpeg(client: AsyncClient, db_session: AsyncSession):
    """1. Upload valid JPEG image succeeds with metadata and status."""
    _u, _p, token = await _create_patient_user(db_session, "user1@test.com")
    jpeg_bytes = make_sample_image_bytes("JPEG")

    files = {"file": ("rx.jpg", jpeg_bytes, "image/jpeg")}
    data = {"document_type": "prescription", "process_immediately": "false"}

    res = await client.post(
        "/api/v1/medical-documents",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    payload = res.json()
    assert payload["file_name"] == "rx.jpg"
    assert payload["document_type"] == "prescription"
    assert payload["mime_type"] == "image/jpeg"
    assert payload["ocr_status"] == "pending"


@pytest.mark.asyncio
async def test_02_upload_supported_png(client: AsyncClient, db_session: AsyncSession):
    """2. Upload valid PNG image succeeds."""
    _u, _p, token = await _create_patient_user(db_session, "user2@test.com")
    png_bytes = make_sample_image_bytes("PNG")

    files = {"file": ("report.png", png_bytes, "image/png")}
    data = {"document_type": "lab_report", "process_immediately": "false"}

    res = await client.post(
        "/api/v1/medical-documents",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    assert res.json()["mime_type"] == "image/png"


@pytest.mark.asyncio
async def test_03_upload_supported_pdf(client: AsyncClient, db_session: AsyncSession):
    """3. Upload valid PDF document succeeds."""
    _u, _p, token = await _create_patient_user(db_session, "user3@test.com")
    pdf_bytes = make_sample_pdf_bytes()

    files = {"file": ("summary.pdf", pdf_bytes, "application/pdf")}
    data = {"document_type": "discharge_summary", "process_immediately": "false"}

    res = await client.post(
        "/api/v1/medical-documents",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    assert res.json()["mime_type"] == "application/pdf"


@pytest.mark.asyncio
async def test_04_upload_unsupported_extension_rejected(client: AsyncClient, db_session: AsyncSession):
    """4. Unsupported file extension (.exe, .txt) rejected with HTTP 400."""
    _u, _p, token = await _create_patient_user(db_session, "user4@test.com")

    files = {"file": ("malware.exe", b"MZ\x90\x00somecode", "application/octet-stream")}
    res = await client.post(
        "/api/v1/medical-documents",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 400
    assert "Unsupported file extension" in res.json()["detail"]


@pytest.mark.asyncio
async def test_05_upload_spoofed_mime_type_rejected(client: AsyncClient, db_session: AsyncSession):
    """5. Spoofed extension with mismatched magic bytes is rejected."""
    _u, _p, token = await _create_patient_user(db_session, "user5@test.com")

    # Plain text content disguised as a .pdf extension
    files = {"file": ("fake.pdf", b"This is plain text pretending to be PDF", "application/pdf")}
    res = await client.post(
        "/api/v1/medical-documents",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 400
    assert "supported binary format" in res.json()["detail"]


@pytest.mark.asyncio
async def test_06_upload_empty_file_rejected(client: AsyncClient, db_session: AsyncSession):
    """6. Empty (0-byte) file upload is rejected with HTTP 400."""
    _u, _p, token = await _create_patient_user(db_session, "user6@test.com")

    files = {"file": ("empty.pdf", b"", "application/pdf")}
    res = await client.post(
        "/api/v1/medical-documents",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 400
    assert "empty" in res.json()["detail"]


@pytest.mark.asyncio
async def test_07_upload_oversized_file_rejected(client: AsyncClient, db_session: AsyncSession):
    """7. File exceeding maximum allowed size is rejected with HTTP 413."""
    _u, _p, token = await _create_patient_user(db_session, "user7@test.com")

    # Mock settings.MEDICAL_DOCUMENT_MAX_SIZE_MB = 1
    with patch("app.documents.service.settings.MEDICAL_DOCUMENT_MAX_SIZE_MB", 1):
        big_content = b"%PDF-" + b"0" * (2 * 1024 * 1024)
        files = {"file": ("giant.pdf", big_content, "application/pdf")}
        res = await client.post(
            "/api/v1/medical-documents",
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 413


@pytest.mark.asyncio
async def test_08_path_traversal_filename_sanitized(client: AsyncClient, db_session: AsyncSession):
    """8. Filename with path traversal sequences is sanitized without escaping storage."""
    _u, _p, token = await _create_patient_user(db_session, "user8@test.com")
    pdf_bytes = make_sample_pdf_bytes()

    files = {"file": ("../../../../etc/passwd.pdf", pdf_bytes, "application/pdf")}
    data = {"process_immediately": "false"}

    res = await client.post(
        "/api/v1/medical-documents",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    saved_filename = res.json()["file_name"]
    assert "/" not in saved_filename
    assert ".." not in saved_filename


@pytest.mark.asyncio
async def test_09_dangerous_filename_characters_sanitized(client: AsyncClient, db_session: AsyncSession):
    """9. Dangerous characters (null bytes, backslashes) in filename are stripped."""
    _u, _p, token = await _create_patient_user(db_session, "user9@test.com")
    png_bytes = make_sample_image_bytes("PNG")

    files = {"file": ("bad\0name\\doc.png", png_bytes, "image/png")}
    data = {"process_immediately": "false"}

    res = await client.post(
        "/api/v1/medical-documents",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    assert "\0" not in res.json()["file_name"]
    assert "\\" not in res.json()["file_name"]


@pytest.mark.asyncio
async def test_10_duplicate_filenames_safe_unique_keys(client: AsyncClient, db_session: AsyncSession):
    """10. Uploading identical filenames creates two distinct records with unique storage paths."""
    _u, _p, token = await _create_patient_user(db_session, "user10@test.com")
    pdf_bytes = make_sample_pdf_bytes()

    files1 = {"file": ("prescription.pdf", pdf_bytes, "application/pdf")}
    files2 = {"file": ("prescription.pdf", pdf_bytes, "application/pdf")}

    res1 = await client.post(
        "/api/v1/medical-documents",
        files=files1,
        data={"process_immediately": "false"},
        headers={"Authorization": f"Bearer {token}"},
    )
    res2 = await client.post(
        "/api/v1/medical-documents",
        files=files2,
        data={"process_immediately": "false"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res1.status_code == 201
    assert res2.status_code == 201
    doc1_id = res1.json()["id"]
    doc2_id = res2.json()["id"]
    assert doc1_id != doc2_id

    # Verify both exist in DB with different file_url paths
    stmt = select(MedicalDocument).where(MedicalDocument.id.in_([uuid.UUID(doc1_id), uuid.UUID(doc2_id)]))
    docs = list((await db_session.execute(stmt)).scalars().all())
    assert len(docs) == 2
    assert docs[0].file_url != docs[1].file_url


@pytest.mark.asyncio
async def test_11_cross_patient_access_blocked(client: AsyncClient, db_session: AsyncSession):
    """11. Patient A cannot view or list Patient B's document (returns safe 404)."""
    _u1, _p1, token1 = await _create_patient_user(db_session, "patientA@test.com")
    _u2, _p2, token2 = await _create_patient_user(db_session, "patientB@test.com")

    # Patient A uploads a document
    res_up = await client.post(
        "/api/v1/medical-documents",
        files={"file": ("reportA.pdf", make_sample_pdf_bytes(), "application/pdf")},
        data={"process_immediately": "false"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    doc_id = res_up.json()["id"]

    # Patient B tries to get document metadata -> 404
    res_b = await client.get(
        f"/api/v1/medical-documents/{doc_id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert res_b.status_code == 404

    # Patient B lists documents -> does not see Patient A's document
    res_list = await client.get(
        "/api/v1/medical-documents",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert res_list.status_code == 200
    ids = [item["id"] for item in res_list.json()["items"]]
    assert doc_id not in ids


@pytest.mark.asyncio
async def test_12_unauthorized_download_blocked(client: AsyncClient, db_session: AsyncSession):
    """12. Unauthenticated or unauthorized caller cannot download binary file."""
    _u1, _p1, token1 = await _create_patient_user(db_session, "patient12@test.com")
    _u2, _p2, token2 = await _create_patient_user(db_session, "intruder@test.com")

    res_up = await client.post(
        "/api/v1/medical-documents",
        files={"file": ("secret.pdf", make_sample_pdf_bytes(), "application/pdf")},
        data={"process_immediately": "false"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    doc_id = res_up.json()["id"]

    # Anonymous download -> 401
    res_anon = await client.get(f"/api/v1/medical-documents/{doc_id}/file")
    assert res_anon.status_code == 401

    # Cross-patient download -> 404
    res_intruder = await client.get(
        f"/api/v1/medical-documents/{doc_id}/file",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert res_intruder.status_code == 404


@pytest.mark.asyncio
async def test_13_patient_can_access_own_document_and_download(client: AsyncClient, db_session: AsyncSession):
    """13. Patient can view metadata and download the exact binary bytes of their own document."""
    _u, _p, token = await _create_patient_user(db_session, "owner@test.com")
    pdf_content = make_sample_pdf_bytes("Unique Patient Clinical Content")

    res_up = await client.post(
        "/api/v1/medical-documents",
        files={"file": ("my_record.pdf", pdf_content, "application/pdf")},
        data={"process_immediately": "false"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_up.status_code == 201
    doc_id = res_up.json()["id"]

    # Get metadata
    res_meta = await client.get(
        f"/api/v1/medical-documents/{doc_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_meta.status_code == 200
    assert res_meta.json()["file_name"] == "my_record.pdf"

    # Download file binary
    res_down = await client.get(
        f"/api/v1/medical-documents/{doc_id}/file",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_down.status_code == 200
    assert res_down.content == pdf_content


@pytest.mark.asyncio
async def test_14_hospital_user_authorization(client: AsyncClient, db_session: AsyncSession):
    """14. Hospital doctor can access consultation documents; staff from another hospital gets 404."""
    hosp1 = await _create_test_hospital(db_session, "Hospital One")
    hosp2 = await _create_test_hospital(db_session, "Hospital Two")

    _doc_u1, _doc_h1, token_doc1 = await _create_hospital_staff_user(db_session, hosp1.id, "doc1@hosp1.com")
    _doc_u2, _doc_h2, token_doc2 = await _create_hospital_staff_user(db_session, hosp2.id, "doc2@hosp2.com")
    _pat_u, patient, pat_token = await _create_patient_user(db_session, "pat14@test.com")

    # Create consultation at Hospital One
    cons = await _create_consultation(db_session, patient.id, hosp1.id)

    # Patient uploads document linked to this consultation
    res_up = await client.post(
        "/api/v1/medical-documents",
        files={"file": ("cons_doc.pdf", make_sample_pdf_bytes(), "application/pdf")},
        data={"consultation_id": str(cons.id), "process_immediately": "false"},
        headers={"Authorization": f"Bearer {pat_token}"},
    )
    doc_id = res_up.json()["id"]

    # Doctor 1 at Hospital One CAN access -> 200
    res_h1 = await client.get(
        f"/api/v1/medical-documents/{doc_id}",
        headers={"Authorization": f"Bearer {token_doc1}"},
    )
    assert res_h1.status_code == 200

    # Doctor 2 at Hospital Two CANNOT access -> 404
    res_h2 = await client.get(
        f"/api/v1/medical-documents/{doc_id}",
        headers={"Authorization": f"Bearer {token_doc2}"},
    )
    assert res_h2.status_code == 404


@pytest.mark.asyncio
async def test_15_invalid_consultation_association_rejected(client: AsyncClient, db_session: AsyncSession):
    """15. Attaching a document to another patient's consultation is rejected with 404."""
    _u1, p1, token1 = await _create_patient_user(db_session, "p1@test.com")
    _u2, p2, _token2 = await _create_patient_user(db_session, "p2@test.com")
    hosp = await _create_test_hospital(db_session)

    # Consultation belongs to p2
    cons_p2 = await _create_consultation(db_session, p2.id, hosp.id)

    # Patient 1 attempts to upload document linked to p2's consultation
    files = {"file": ("report.pdf", make_sample_pdf_bytes(), "application/pdf")}
    data = {"consultation_id": str(cons_p2.id), "process_immediately": "false"}

    res = await client.post(
        "/api/v1/medical-documents",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert res.status_code == 404


# ===========================================================================
# PART 26: OCR LAYER TESTS (16 - 23)
# ===========================================================================


@pytest.mark.asyncio
async def test_16_ocr_success_mock(client: AsyncClient, db_session: AsyncSession):
    """16. Mocked OCR provider produces extracted text and completed ocr_status."""
    _u, _p, token = await _create_patient_user(db_session, "ocr16@test.com")
    png_bytes = make_sample_image_bytes("PNG")

    mock_ocr = OCRResult(
        text="Dr. Sharma Prescription\nTab Metformin 500mg once daily\nTab Telmisartan 40mg once daily",
        pages=[OCRPageResult(page_number=1, text="Dr. Sharma Prescription", confidence=0.92)],
        provider="mock_tesseract",
        language="eng",
        confidence=0.92,
        warnings=[],
        metadata={"character_count": 80, "page_count": 1},
    )

    with patch.object(document_processor, "extract_document_text", new_callable=AsyncMock) as mock_extract:
        mock_extract.return_value = mock_ocr
        res = await client.post(
            "/api/v1/medical-documents",
            files={"file": ("rx.png", png_bytes, "image/png")},
            data={"process_immediately": "true"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201
        assert res.json()["ocr_status"] == "completed"


@pytest.mark.asyncio
async def test_17_ocr_empty_result_warning(client: AsyncClient, db_session: AsyncSession):
    """17. Empty OCR result records warning and keeps document."""
    _u, _p, token = await _create_patient_user(db_session, "ocr17@test.com")
    png_bytes = make_sample_image_bytes("PNG")

    empty_ocr = OCRResult(
        text="",
        pages=[],
        provider="mock_tesseract",
        warnings=["No readable text could be identified in this document."],
    )

    with patch.object(document_processor, "extract_document_text", new_callable=AsyncMock) as mock_extract:
        mock_extract.return_value = empty_ocr
        res = await client.post(
            "/api/v1/medical-documents",
            files={"file": ("blank.png", png_bytes, "image/png")},
            data={"process_immediately": "true"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201
        doc_id = res.json()["id"]

        ext_res = await client.get(
            f"/api/v1/medical-documents/{doc_id}/extraction",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert ext_res.status_code == 200
        assert any("no readable text" in w.lower() for w in ext_res.json()["warnings"])


@pytest.mark.asyncio
async def test_18_ocr_provider_failure_handled(client: AsyncClient, db_session: AsyncSession):
    """18. OCR failure sets ocr_status='failed', preserves document, does not crash."""
    _u, _p, token = await _create_patient_user(db_session, "ocr18@test.com")
    png_bytes = make_sample_image_bytes("PNG")

    with patch.object(document_processor, "extract_document_text", new_callable=AsyncMock) as mock_extract:
        mock_extract.side_effect = OCRError("Binary crashed", provider="tesseract", category="ocr_crash")
        res = await client.post(
            "/api/v1/medical-documents",
            files={"file": ("corrupt.png", png_bytes, "image/png")},
            data={"process_immediately": "true"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201
        payload = res.json()
        assert payload["ocr_status"] == "failed"
        assert payload["processing_status"] == "failed"


@pytest.mark.asyncio
async def test_19_ocr_metadata_preserved():
    """19. OCRResult preserves metadata such as character count and confidence."""
    res = OCRResult(
        text="Hello Clinova OCR",
        pages=[OCRPageResult(page_number=1, text="Hello Clinova OCR", confidence=0.95)],
        provider="tesseract",
        confidence=0.95,
        metadata={"processing_seconds": 0.35},
    )
    assert res.character_count == 17
    assert res.page_count == 1
    assert res.confidence == 0.95


@pytest.mark.asyncio
async def test_20_multi_page_document_handling():
    """20. Multi-page document preserves page numbers and full text."""
    p1 = OCRPageResult(page_number=1, text="Page 1 Content", confidence=0.9)
    p2 = OCRPageResult(page_number=2, text="Page 2 Content", confidence=0.88)
    res = OCRResult(text="Page 1 Content\n\nPage 2 Content", pages=[p1, p2])
    assert res.page_count == 2
    assert res.pages[1].page_number == 2


@pytest.mark.asyncio
async def test_21_language_configuration_passed():
    """21. Language configuration is respected by document processor."""
    from app.documents.ocr.base import OCRProvider

    class DummyOCR(OCRProvider):
        @property
        def name(self):
            return "dummy"

        async def extract_text(self, file_path, mime_type, language="eng"):
            return OCRResult(text="मराठी मजकूर", language=language)

        def supported_mime_types(self):
            return {"image/png"}

    proc = document_processor.__class__(ocr_provider=DummyOCR())
    res = await proc.extract_document_text(Path("dummy.png"), "image/png", language="mar")
    assert res.language == "mar"


@pytest.mark.asyncio
async def test_22_digital_pdf_embedded_text_extraction(tmp_path: Path):
    """22. Digital PDF extracts embedded text directly via pypdf without OCR overhead."""
    pdf_file = tmp_path / "digital_test.pdf"
    pdf_file.write_bytes(make_sample_pdf_bytes("Digital Text from pypdf Extraction"))

    res = await document_processor.extract_document_text(pdf_file, "application/pdf")
    assert res is not None
    assert res.provider == "pypdf_embedded"
    assert "Digital Text" in res.text


@pytest.mark.asyncio
async def test_23_ocr_retry_behavior(client: AsyncClient, db_session: AsyncSession):
    """23. POST /process allows retrying a previously failed or pending document."""
    _u, _p, token = await _create_patient_user(db_session, "retry23@test.com")
    pdf_bytes = make_sample_pdf_bytes("Retry Clinical Text")

    # Upload with process_immediately=false
    res_up = await client.post(
        "/api/v1/medical-documents",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        data={"process_immediately": "false"},
        headers={"Authorization": f"Bearer {token}"},
    )
    doc_id = res_up.json()["id"]
    assert res_up.json()["ocr_status"] == "pending"

    # Now trigger processing via POST /process
    res_proc = await client.post(
        f"/api/v1/medical-documents/{doc_id}/process",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_proc.status_code == 200
    assert res_proc.json()["ocr_status"] == "completed"


@pytest.mark.asyncio
async def test_23b_tesseract_ocr_provider_output_types(tmp_path: Path):
    """23b. TesseractOCRProvider gracefully handles dict, bytes, and string pytesseract returns."""
    from app.documents.ocr.tesseract import TesseractOCRProvider

    img_path = tmp_path / "test_ocr.png"
    img_path.write_bytes(make_sample_image_bytes("PNG"))

    provider = TesseractOCRProvider()

    # 1. Standard string output
    with patch("pytesseract.image_to_string", return_value="Standard OCR text"), \
         patch("pytesseract.image_to_data", return_value={"conf": ["95", "90"]}):
        res = await provider.extract_text(img_path, "image/png")
        assert res.text == "Standard OCR text"
        assert res.confidence == 0.925

    # 2. Dict output (e.g. if Output.DICT was used or mocked as dict)
    with patch("pytesseract.image_to_string", return_value={"text": "Dict OCR text"}), \
         patch("pytesseract.image_to_data", return_value={"conf": []}):
        res = await provider.extract_text(img_path, "image/png")
        assert res.text == "Dict OCR text"
        assert res.confidence is None

    # 3. Bytes output
    with patch("pytesseract.image_to_string", return_value=b"Bytes OCR text"), \
         patch("pytesseract.image_to_data", return_value={"conf": ["80"]}):
        res = await provider.extract_text(img_path, "image/png")
        assert res.text == "Bytes OCR text"
        assert res.confidence == 0.8


# ===========================================================================
# PART 27: AI STRUCTURED EXTRACTION TESTS (24 - 32)
# ===========================================================================


@pytest.mark.asyncio
async def test_24_ai_structured_extraction_success(client: AsyncClient, db_session: AsyncSession):
    """24. Valid AI response is parsed and stored into DocumentExtraction model."""
    _u, _p, token = await _create_patient_user(db_session, "ai24@test.com")
    pdf_bytes = make_sample_pdf_bytes("Prescription: Tab Metformin 500mg TDS after meals")

    mock_ai_json = {
        "document_type": "prescription",
        "document_date": "2026-09-01",
        "hospital_or_clinic_name": "Apollo Clinic",
        "doctor_name": "Dr. R. Mehta",
        "diagnoses_or_conditions_as_documented": ["Type 2 Diabetes Mellitus"],
        "medications": [
            {
                "name_as_written": "Metformin",
                "dose_as_written": "500mg",
                "frequency_as_written": "TDS",
                "instructions_as_written": "after meals",
                "source_page": 1,
                "evidence": "Tab Metformin 500mg TDS after meals",
                "is_uncertain": False,
            }
        ],
        "laboratory_results": [],
    }

    ai_resp = AIResponse(
        text=f"```json\n{json.dumps(mock_ai_json)}\n```",
        provider="gemini",
        model="gemini-2.0-flash",
    )

    with patch.object(task_router, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = ai_resp
        res = await client.post(
            "/api/v1/medical-documents",
            files={"file": ("rx.pdf", pdf_bytes, "application/pdf")},
            data={"process_immediately": "true"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201
        doc_id = res.json()["id"]

        ext_res = await client.get(
            f"/api/v1/medical-documents/{doc_id}/extraction",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert ext_res.status_code == 200
        data = ext_res.json()["extracted_data"]
        assert data["diagnoses_or_conditions_as_documented"] == ["Type 2 Diabetes Mellitus"]
        assert len(data["medications"]) == 1
        assert data["medications"][0]["name_as_written"] == "Metformin"
        assert data["medications"][0]["evidence"] == "Tab Metformin 500mg TDS after meals"


@pytest.mark.asyncio
async def test_25_missing_optional_fields_defaulted():
    """25. DocumentExtraction schema gracefully defaults omitted optional fields to empty/null."""
    minimal_json = {
        "document_type": "prescription",
        "medications": [],
    }
    extracted = DocumentExtraction.model_validate(minimal_json)
    assert extracted.diagnoses_or_conditions_as_documented == []
    assert extracted.symptoms_as_documented == []
    assert extracted.laboratory_results == []
    assert extracted.doctor_name is None


@pytest.mark.asyncio
async def test_26_ai_malformed_json_handled_gracefully(client: AsyncClient, db_session: AsyncSession):
    """26. Malformed JSON from AI model does not crash; records warning and marks extraction failed."""
    _u, _p, token = await _create_patient_user(db_session, "ai26@test.com")
    pdf_bytes = make_sample_pdf_bytes("Clinical text")

    ai_resp = AIResponse(
        text="This is not JSON at all: { broken json ...",
        provider="gemini",
        model="gemini-2.0-flash",
    )

    with patch.object(task_router, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = ai_resp
        res = await client.post(
            "/api/v1/medical-documents",
            files={"file": ("malformed.pdf", pdf_bytes, "application/pdf")},
            data={"process_immediately": "true"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201
        doc_id = res.json()["id"]

        ext_res = await client.get(
            f"/api/v1/medical-documents/{doc_id}/extraction",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert ext_res.status_code == 200
        assert ext_res.json()["extraction_status"] == "failed"
        assert any("json" in w.lower() for w in ext_res.json()["warnings"])


@pytest.mark.asyncio
async def test_27_ai_schema_validation_error_handled(client: AsyncClient, db_session: AsyncSession):
    """27. AI response violating Pydantic schema is caught safely."""
    _u, _p, token = await _create_patient_user(db_session, "ai27@test.com")
    pdf_bytes = make_sample_pdf_bytes("Clinical text")

    # medications must be list of MedicationExtraction dicts; here given a string
    invalid_schema_json = {
        "medications": "Tab Paracetamol 500mg",
    }
    ai_resp = AIResponse(
        text=json.dumps(invalid_schema_json),
        provider="gemini",
        model="gemini-2.0-flash",
    )

    with patch.object(task_router, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = ai_resp
        res = await client.post(
            "/api/v1/medical-documents",
            files={"file": ("invalid_schema.pdf", pdf_bytes, "application/pdf")},
            data={"process_immediately": "true"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201
        doc_id = res.json()["id"]

        ext_res = await client.get(
            f"/api/v1/medical-documents/{doc_id}/extraction",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert ext_res.status_code == 200
        assert ext_res.json()["extraction_status"] == "failed"


@pytest.mark.asyncio
async def test_28_ai_provider_timeout_or_error(client: AsyncClient, db_session: AsyncSession):
    """28. AI Provider error (timeout/network) preserves OCR text and records safe failed status."""
    _u, _p, token = await _create_patient_user(db_session, "ai28@test.com")
    pdf_bytes = make_sample_pdf_bytes("Important lab report text: Hb 11.2")

    with patch.object(task_router, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = AIProviderError(
            kind=AIErrorKind.TIMEOUT,
            message="Provider timed out after 30s",
            provider="gemini",
        )
        res = await client.post(
            "/api/v1/medical-documents",
            files={"file": ("timeout_report.pdf", pdf_bytes, "application/pdf")},
            data={"process_immediately": "true"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201
        doc_id = res.json()["id"]

        ext_res = await client.get(
            f"/api/v1/medical-documents/{doc_id}/extraction",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert ext_res.status_code == 200
        # OCR text is preserved!
        assert "Important lab report text" in ext_res.json()["raw_ocr_text"]
        assert ext_res.json()["extraction_status"] == "failed"
        assert any("timed out" in w.lower() for w in ext_res.json()["warnings"])


@pytest.mark.asyncio
async def test_29_all_ai_providers_unavailable_fallback(client: AsyncClient, db_session: AsyncSession):
    """29. If all AI providers fail, OCR text is safely retained and app remains healthy."""
    _u, _p, token = await _create_patient_user(db_session, "ai29@test.com")
    pdf_bytes = make_sample_pdf_bytes("Patient has normal ECG")

    with patch.object(task_router, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = AIProviderError(
            kind=AIErrorKind.PROVIDER_UNAVAILABLE,
            message="All AI providers exhausted",
            provider="ollama",
        )
        res = await client.post(
            "/api/v1/medical-documents",
            files={"file": ("ecg.pdf", pdf_bytes, "application/pdf")},
            data={"process_immediately": "true"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201
        assert res.json()["ocr_status"] == "completed"


@pytest.mark.asyncio
async def test_30_extraction_contains_source_supported_fields_only():
    """30. Non-diagnostic extraction: only documented diagnoses are retained."""
    raw = {
        "diagnoses_or_conditions_as_documented": ["Essential Hypertension"],
        "medications": [],
        "laboratory_results": [],
    }
    extracted = DocumentExtraction.model_validate(raw)
    assert extracted.diagnoses_or_conditions_as_documented == ["Essential Hypertension"]


@pytest.mark.asyncio
async def test_31_medication_extraction_with_uncertainty():
    """31. Medication extraction supports handwritten/uncertain flag and evidence."""
    med = MedicationExtraction(
        name_as_written="Augmentin?",
        dose_as_written="625mg",
        evidence="Augmentin? 625 BD",
        is_uncertain=True,
    )
    assert med.is_uncertain is True
    assert med.evidence == "Augmentin? 625 BD"


@pytest.mark.asyncio
async def test_32_lab_result_extraction():
    """32. Laboratory result extraction captures test, value, unit, and evidence."""
    lab = LabResultExtraction(
        test_name="Serum Creatinine",
        value="1.1",
        unit="mg/dL",
        reference_range="0.7 - 1.2 mg/dL",
        abnormal_flag_as_documented=None,
        evidence="Serum Creatinine: 1.1 mg/dL (Ref: 0.7-1.2)",
    )
    assert lab.test_name == "Serum Creatinine"
    assert lab.value == "1.1"
    assert lab.unit == "mg/dL"


# ===========================================================================
# PART 28: INTEGRATION & E2E TESTS (33 - 35)
# ===========================================================================


@pytest.mark.asyncio
async def test_33_end_to_end_upload_ocr_ai_extraction_flow(client: AsyncClient, db_session: AsyncSession):
    """33. Full pipeline: Upload -> OCR -> AI structured extraction -> DB persistence -> GET extraction."""
    _u, _p, token = await _create_patient_user(db_session, "e2e33@test.com")
    pdf_bytes = make_sample_pdf_bytes("Hospital Lab Report: Hemoglobin 10.2 g/dL. Diagnosed with Mild Anemia.")

    mock_ai_json = {
        "document_type": "lab_report",
        "document_date": "2026-09-02",
        "hospital_or_clinic_name": "General Diagnostic Lab",
        "diagnoses_or_conditions_as_documented": ["Mild Anemia"],
        "laboratory_results": [
            {
                "test_name": "Hemoglobin",
                "value": "10.2",
                "unit": "g/dL",
                "reference_range": "12.0 - 15.0 g/dL",
                "abnormal_flag_as_documented": "LOW",
                "source_page": 1,
                "evidence": "Hemoglobin 10.2 g/dL",
            }
        ],
    }
    ai_resp = AIResponse(
        text=json.dumps(mock_ai_json),
        provider="gemini",
        model="gemini-2.0-flash",
    )

    with patch.object(task_router, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = ai_resp
        # Step 1: Upload document
        upload_res = await client.post(
            "/api/v1/medical-documents",
            files={"file": ("cbc_report.pdf", pdf_bytes, "application/pdf")},
            data={"document_type": "lab_report", "process_immediately": "true"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert upload_res.status_code == 201
        doc_id = upload_res.json()["id"]

        # Step 2: GET document extraction
        ext_res = await client.get(
            f"/api/v1/medical-documents/{doc_id}/extraction",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert ext_res.status_code == 200
        ext_payload = ext_res.json()
        assert ext_payload["extraction_status"] == "completed"
        assert "Hemoglobin" in ext_payload["raw_ocr_text"]

        extracted = ext_payload["extracted_data"]
        assert extracted["diagnoses_or_conditions_as_documented"] == ["Mild Anemia"]
        assert len(extracted["laboratory_results"]) == 1
        assert extracted["laboratory_results"][0]["test_name"] == "Hemoglobin"
        assert extracted["laboratory_results"][0]["value"] == "10.2"
        assert extracted["laboratory_results"][0]["evidence"] == "Hemoglobin 10.2 g/dL"


@pytest.mark.asyncio
async def test_34_ocr_failure_preserves_original_document(client: AsyncClient, db_session: AsyncSession):
    """34. When OCR fails, original document is preserved on disk and still downloadable."""
    _u, _p, token = await _create_patient_user(db_session, "e2e34@test.com")
    png_bytes = make_sample_image_bytes("PNG")

    with patch.object(document_processor, "extract_document_text", new_callable=AsyncMock) as mock_extract:
        mock_extract.side_effect = OCRError("OCR Engine Failure", provider="tesseract")
        res = await client.post(
            "/api/v1/medical-documents",
            files={"file": ("failed_ocr.png", png_bytes, "image/png")},
            data={"process_immediately": "true"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201
        doc_id = res.json()["id"]
        assert res.json()["ocr_status"] == "failed"

        # Original document is still downloadable!
        down_res = await client.get(
            f"/api/v1/medical-documents/{doc_id}/file",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert down_res.status_code == 200
        assert down_res.content == png_bytes


@pytest.mark.asyncio
async def test_35_ai_failure_preserves_ocr_and_document(client: AsyncClient, db_session: AsyncSession):
    """35. When AI extraction fails, OCR text and original document are safely preserved."""
    _u, _p, token = await _create_patient_user(db_session, "e2e35@test.com")
    pdf_bytes = make_sample_pdf_bytes("Important Discharge Summary Text")

    with patch.object(task_router, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = Exception("LLM connection severed")
        res = await client.post(
            "/api/v1/medical-documents",
            files={"file": ("summary.pdf", pdf_bytes, "application/pdf")},
            data={"process_immediately": "true"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201
        doc_id = res.json()["id"]

        ext_res = await client.get(
            f"/api/v1/medical-documents/{doc_id}/extraction",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert ext_res.status_code == 200
        payload = ext_res.json()
        assert payload["ocr_status"] == "completed"
        assert payload["extraction_status"] == "failed"
        assert "Important Discharge Summary Text" in payload["raw_ocr_text"]
