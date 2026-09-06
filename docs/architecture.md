# Clinova Architecture Overview

## Phase 1: Foundation & Authentication

Clinova uses a clean monorepo architecture with a centralized Python FastAPI backend serving three independent client applications backed by PostgreSQL.

### Core Entity Relationships

```
USER
 ├── PATIENT  -> patient_profiles (1:1)
 └── HOSPITAL -> hospitals        (1:1)
 └── refresh_tokens               (1:N)
```

### Client Applications

1. **Patient Web (`clients/patient-web`)**:
   - Technology: React + TypeScript + Vite + TanStack Query
   - Audience: Patients accessing through desktop and web browsers

2. **Hospital Web (`clients/hospital-web`)**:
   - Technology: React + TypeScript + Vite + TanStack Query
   - Audience: Hospital administrative and facility personnel

3. **Patient Mobile (`clients/patient-mobile`)**:
   - Technology: React Native + Expo + TypeScript
   - Audience: Patients accessing through mobile devices (iOS / Android)

### Backend Service (`backend/`)

- Framework: FastAPI
- Data Layer: SQLAlchemy 2.0 Async + asyncpg
- Schema Migrations: Alembic
- Cryptography: Argon2id (`pwdlib[argon2]`) + PyJWT

---

## Step 7 — Medical Document Processing

```
Upload
  ↓
Secure storage (LocalStorageProvider / path traversal defense)
  ↓
OCR / text extraction (pypdf digital PDF / Tesseract image OCR)
  ↓
Structured AI extraction (AITaskType.STRUCTURED_EXTRACTION via AITaskRouter)
  ↓
Evidence-backed ExtractedData (DocumentExtraction schema)
  ↓
Ready for future Medical Timeline (Step 8)
```

### Key Principles:
1. **Original Document Preservation**: The original uploaded file is safely stored on disk and remains intact and accessible even if OCR or AI structured extraction fails.
2. **Strictly Non-Diagnostic**: The extraction engine structures explicitly documented findings only. It never diagnoses conditions from lab values or symptoms, and never recommends medications.
3. **No Fabrication of Clinical Data**: Absent fields remain null/empty. Uncertain handwriting or blurry text is explicitly marked (`is_uncertain=True`).
4. **Evidence & Page Traceability**: Extracted items are accompanied by their source page number and the exact OCR text snippet.
5. **Multi-Provider AI Fallback**: Structured extraction routes through the existing `AITaskRouter` fallback chain (Task Provider → Default Cloud Provider → Groq/OpenRouter → Ollama as the LAST fallback).
6. **Robust Failure Resilience**: OCR failure preserves the original document; AI failure preserves the OCR text and original document with a safe processing status.

---

## Step 8 — Medical Timeline

```
Clinical History
       +
AI Interview Statements
       +
Medical Documents & ExtractedData
       +
Consultation Encounters
       ↓
Timeline Builders (Consultation, ClinicalHistory, AIInterview, Document)
       ↓
Deterministic Normalization & Deduplication
       ↓
Idempotent Timeline Synchronization (TimelineEvent Table)
       ↓
Chronological Patient Medical Timeline (GET /api/v1/patients/me/timeline)
```

### Key Architectural Principles:
1. **Source-Backed & Non-Diagnostic**: Timeline organizes historical facts without inferring diagnoses, prognoses, or treatment compliance. It reflects what was documented or reported, not deductions.
2. **No Invented Dates**: Dates maintain strict precision (`EXACT`, `MONTH`, `YEAR`, `APPROXIMATE`, `UNKNOWN`). Relative or fuzzy statements (e.g. "about 5 years ago") remain approximate with no fabricated calendar dates.
3. **Strict Provenance**: Every event preserves `source_type` (`PATIENT_HISTORY`, `AI_INTERVIEW`, `MEDICAL_DOCUMENT`, `OCR_EXTRACTION`, `CONSULTATION`, `CLINICIAN_ENTERED`), `source_id`, source page number, and original supporting textual evidence.
4. **Distinct Clinical Authority**: Patient-reported statements remain `UNVERIFIED` and cannot be converted to `CLINICIAN_VERIFIED` by patients. Document extractions remain `SOURCE_CONFIRMED` until reviewed by licensed physicians.
5. **Idempotent Rebuild**: Rebuilding the timeline via `POST /api/v1/patients/me/timeline/rebuild` reconciles existing and new events deterministically without duplicate database rows.
7. **Step 9 Bridge**: Structured timeline events provide direct foundation for the Step 9 Clinical Summary + Physician Review workflows, where clinician confirmation promotes events to `CLINICIAN_VERIFIED`.

---

## Step 9: AI Clinical Summary & Physician Review Dashboard

```
Existing Clinical Data Streams
(History + AI Interview + Medical Timeline + Documents/OCR + Consultations + Triage Alerts)
                       ↓
         Evidence/Context Assembly (`ClinicalContextAssembler`)
                       ↓
         AI Summary Generator (`task_router.generate(AITaskType.CLINICAL_SUMMARY)`)
                       ↓ (Guaranteed deterministic grounded fallback if AI is offline)
         Pydantic Strict Validation (`StructuredSummary`)
                       ↓
         Draft Summary Table (`Summary`, status="draft", ai_draft_text saved)
                       ↓
               Physician Review
         ┌─────────────┼─────────────┐
         ↓             ↓             ↓
    Edit Draft    Reject Draft  Confirm/Finalize
         │             │             │
         │             │             ▼
         │             │      Finalized Summary (`status="confirmed"`)
         │             │      + Audit Log (`summary_confirmed`)
         │             │      + Consultation status -> `reviewed`
         │             │      + Timeline events -> `CLINICIAN_VERIFIED`
         │             ▼
         │       Rejected Draft (`status="rejected"`, `rejection_reason`)
         ▼
    Updated Draft (`status="draft"`, version+1, `clinician_notes`)
    + Original AI draft preserved in `ai_draft_text`
```

### Key Principles:
1. **AI Drafts, Physician Decides**: Summary draft is an assistive synthesis tool for licensed physicians. AI never diagnoses or prescribes.
2. **Provenance & Source Attribution**: Every observation is tagged with its source type (`PATIENT_REPORTED`, `DOCUMENT_EXTRACTED`, `CLINICAL_HISTORY`, `TRIAGE_ALERT`) with verbatim evidence snippets.
3. **Auditability**: Complete audit trail in `audit_logs` tracking creation, edits, confirmation, and rejections.
4. **Multi-Tenant Security**: Patients have read-only access to summaries of their own consultations. Edits, confirmations, and rejections are strictly restricted to authorized hospital clinicians (`403 Forbidden` for patients, `404 Not Found` across hospitals).

