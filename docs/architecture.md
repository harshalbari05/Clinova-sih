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
6. **Robust Multi-Tenant Security**: Patient can only access their own timeline. Hospital staff can access patient timelines only when an active facility consultation relationship exists. Unauthorized cross-patient access returns safe `404 Not Found`.
7. **Step 9 Compatibility**: Structured timeline events provide direct foundation for the upcoming Step 9 Clinical Summary + Physician Review workflows.

