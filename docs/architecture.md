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
