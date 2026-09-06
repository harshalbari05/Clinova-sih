# Clinova Backend API

Central FastAPI backend service handling authentication, role-based access control, and PostgreSQL data persistence for the Clinova platform.

---

## 1. Prerequisites
- **Python**: 3.12+
- **PostgreSQL**: 15+ (Production/staging relational store)
- **Node.js / npm**: Required for client web applications

---

## 2. Authentication Architecture

Clinova utilizes a secure, stateless JWT Bearer token authentication system with bcrypt password hashing:

```
           [ Client Application ]
                     │
    Bearer Token / HTTP Credentials
                     │
                     ▼
             [ FastAPI Router ]
          (/api/v1/auth/...)
                     │
                     ▼
          [ FastAPI Dependencies ]
            (deps.get_current_user)
                     │
                     ▼
          [ AuthService Layer ]
    (Password verification, JWT generation)
                     │
                     ▼
       [ SQLAlchemy 2.0 Async ORM ]
         (User, Patient, Hospital)
                     │
                     ▼
           [ PostgreSQL Database ]
```

### Key Security Features
- **Stateless JWT Tokens**: Signed with HMAC-SHA256 (`HS256`).
- **Minimum Essential Claims**: Token payload contains `sub` (User UUID), `role`, `user_type`, and `hospital_id` (when applicable). Sensitive medical details are never included in tokens.
- **Bcrypt Hashing**: Passwords are encrypted with individual salts. Passwords and hashes are never returned across any API responses.
- **Dual User Flow**:
  - **Patients**: 1-to-1 relationship with `Patient` demographic profile.
  - **Hospitals**: Associated via `HospitalUser` join table with granular roles (`hospital_admin`, `doctor`, `hospital_staff`).

---

## 3. Environment Configuration

The backend reads configuration from `.env` via `pydantic-settings`. Configure the following variables:

```env
# Application
PROJECT_NAME="Clinova API"
API_V1_STR="/api/v1"
ENVIRONMENT="development"
DEBUG=True

# Database Configuration (PostgreSQL Async)
DATABASE_URL="postgresql+asyncpg://postgres:your_secure_password@localhost:5432/clinova_db"
POSTGRES_SERVER="localhost"
POSTGRES_PORT=5432
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="your_secure_password"
POSTGRES_DB="clinova_db"

# JWT & Authentication Configuration
JWT_SECRET_KEY="your_super_secret_jwt_key_min_32_characters_long"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS Allowed Origins
BACKEND_CORS_ORIGINS="http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174"
```

---

## 4. Local Environment Setup

### A. Create Python Virtual Environment
From the `backend/` directory:

```powershell
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### B. Install Dependencies
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### C. Configure Environment Variables
```powershell
# Windows (PowerShell)
Copy-Item .env.example .env

# Linux / macOS
cp .env.example .env
```

---

## 5. Running the Development Server

Start the FastAPI server:

```powershell
uvicorn app.main:app --reload --port 8000
```

The server will be available at `http://localhost:8000`.

---

## 6. Available Authentication Endpoints

| Method | Endpoint | Auth Required | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/patient/register` | No | Register a new patient and user account |
| `POST` | `/api/v1/auth/patient/login` | No | Login patient with email or phone |
| `POST` | `/api/v1/auth/hospital/register` | No | Register a hospital facility and admin user |
| `POST` | `/api/v1/auth/hospital/login` | No | Login hospital staff or admin |
| `GET` | `/api/v1/auth/me` | Bearer JWT | Retrieve profile of authenticated user |
| `POST` | `/api/v1/auth/logout` | No | Stateless logout (client discards token) |
| `GET` | `/api/v1/health` | No | Service health check |
| `GET` | `/api/v1/health/db` | No | Database connection health check |

Interactive OpenAPI documentation:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 7. Example API Requests

### Patient Registration
```bash
curl -X POST "http://localhost:8000/api/v1/auth/patient/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "patient@example.com",
    "phone": "+919876543210",
    "password": "StrongPassword123!",
    "full_name": "Ramesh Kumar",
    "date_of_birth": "1990-05-15",
    "gender": "male",
    "abha_id": "14-1234-5678-9012"
  }'
```

### Patient Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/patient/login" \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "patient@example.com",
    "password": "StrongPassword123!"
  }'
```

### Access Current User Profile (`/me`)
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>"
```

### Hospital Registration
```bash
curl -X POST "http://localhost:8000/api/v1/auth/hospital/register" \
  -H "Content-Type: application/json" \
  -d '{
    "hospital_name": "Apollo Multispecialty Hospital",
    "registration_number": "HOSP-MH-2026-001",
    "hospital_phone": "+912223456789",
    "hospital_email": "contact@apollohospital.org",
    "city": "Mumbai",
    "state": "Maharashtra",
    "pincode": "400001",
    "admin_email": "admin@apollohospital.org",
    "admin_password": "AdminSecurePassword123!",
    "admin_phone": "+919812345678",
    "admin_name": "Dr. Sharma"
  }'
```

### Hospital Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/hospital/login" \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "admin@apollohospital.org",
    "password": "AdminSecurePassword123!"
  }'
```

### Logout
```bash
curl -X POST "http://localhost:8000/api/v1/auth/logout"
```

---

## 8. Running Automated Tests

Run the complete test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Run tests by module:

```powershell
# Authentication only
.\.venv\Scripts\python.exe -m pytest tests/test_auth.py -v

# Patient profile only
.\.venv\Scripts\python.exe -m pytest tests/test_patient.py -v

# Consultations only
.\.venv\Scripts\python.exe -m pytest tests/test_consultations.py -v
```

---

## 9. Patient Profile Endpoints (Step 2)

### Authentication Requirement
Both endpoints require a valid `Bearer` JWT token issued during patient login.

| Method | Endpoint | Auth Required | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/patients/me` | Bearer JWT (Patient) | Return authenticated patient's profile |
| `PUT` | `/api/v1/patients/me` | Bearer JWT (Patient) | Partially update authenticated patient's profile |

### Ownership & Security Rules
- Patient identity is **always derived from the JWT** — no client-supplied `patient_id` is accepted.
- A patient can **only** read or update **their own** profile.
- Passwords and hashes are **never** returned in any response.
- `id`, `user_id`, and `created_at` are **read-only** and not accepted in update payloads.
- Uniqueness on `phone` and `abha_id` is validated before committing; conflicts return `HTTP 409`.

### GET /api/v1/patients/me
```bash
curl -X GET "http://localhost:8000/api/v1/patients/me" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>"
```

**Example Response:**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "user_id": "4ab93c21-...",
  "full_name": "Ramesh Kumar",
  "date_of_birth": "1990-05-15",
  "gender": "male",
  "phone": "+919876543210",
  "abha_id": "14-1234-5678-9012",
  "address": "42 Market Street, Bangalore",
  "emergency_contact": "Sita (+919876543219)",
  "created_at": "2026-09-05T10:00:00Z"
}
```

### PUT /api/v1/patients/me
All fields are optional — only fields provided will be updated (partial update).

```bash
curl -X PUT "http://localhost:8000/api/v1/patients/me" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Ramesh Kumar Updated",
    "address": "99 New Colony, Hyderabad",
    "emergency_contact": "Kavitha (+919900000001)"
  }'
```

**Updatable Fields:** `full_name`, `date_of_birth`, `gender`, `phone`, `abha_id`, `address`, `emergency_contact`

---

## 10. Consultation Endpoints (Step 2)

### Authentication Requirement
All consultation endpoints require a valid `Bearer` JWT for a **patient** account.

| Method | Endpoint | Auth Required | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/consultations` | Bearer JWT (Patient) | Create a new consultation |
| `GET` | `/api/v1/consultations` | Bearer JWT (Patient) | List authenticated patient's consultations |
| `GET` | `/api/v1/consultations/{id}` | Bearer JWT (Patient) | Get a single consultation by ID |

### Ownership & Security Rules
- `patient_id` is **always derived from the authenticated JWT** — clients cannot inject a different `patient_id`.
- A patient can **only** see their own consultations. Attempting to access another patient's consultation returns `HTTP 404` (not 403) to avoid leaking existence information.
- `hospital_id` must reference an existing hospital; an invalid ID returns `HTTP 404`.
- Consultation status defaults to `"initiated"` at creation.

### POST /api/v1/consultations
```bash
curl -X POST "http://localhost:8000/api/v1/consultations" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "hospital_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "chief_complaint": "Persistent headache for 3 days"
  }'
```

**Example Response (HTTP 201):**
```json
{
  "id": "a1b2c3d4-...",
  "patient_id": "4ab93c21-...",
  "hospital_id": "3fa85f64-...",
  "status": "initiated",
  "chief_complaint": "Persistent headache for 3 days",
  "started_at": null,
  "completed_at": null,
  "created_at": "2026-09-05T10:30:00Z",
  "updated_at": "2026-09-05T10:30:00Z"
}
```

### GET /api/v1/consultations
```bash
# Default (20 results, newest first)
curl -X GET "http://localhost:8000/api/v1/consultations" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>"

# With pagination
curl -X GET "http://localhost:8000/api/v1/consultations?limit=10&offset=0" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>"
```

**Example Response:**
```json
{
  "items": [ { "id": "...", "status": "initiated", ... } ],
  "total": 5,
  "limit": 20,
  "offset": 0
}
```

### GET /api/v1/consultations/{consultation_id}
```bash
curl -X GET "http://localhost:8000/api/v1/consultations/a1b2c3d4-..." \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>"
```

---

## 11. HTTP Status Code Reference

| Code | Meaning |
| :--- | :--- |
| `200` | Success |
| `201` | Resource created |
| `401` | Missing or invalid JWT |
| `403` | Authenticated, but wrong account type (e.g., hospital user on patient endpoint) |
| `404` | Resource not found (or ownership denied — to prevent information leakage) |
| `409` | Uniqueness conflict (`phone`, `abha_id`) |
| `422` | Request validation error (Pydantic) |

---

## 12. Implemented Steps

| Step | Feature | Status |
| :--- | :--- | :--- |
| Step 1 | Authentication (Patient + Hospital, JWT, bcrypt) | ✅ Complete |
| Step 2 | Patient Profile + Consultation Management | ✅ Complete |
| Step 3 | Clinical History & AI Interview | 🔜 Not started |
| Step 4 | Document Upload (OCR) | 🔜 Not started |
| Step 5 | Timeline & Summary | 🔜 Not started |
| Step 6 | Hospital Review Dashboard | 🔜 Not started |

> Clinical history, AI interview, OCR document processing, and ABDM integration are **not yet implemented**.

---

## 13. Clinical History Endpoints (Step 3)

Clinical history records are nested under their parent consultation in the URL structure:

```
/api/v1/consultations/{consultation_id}/history
```

### Authentication & Ownership Requirements
- All endpoints require a valid `Bearer` JWT for a **patient** account.
- The ownership chain is enforced server-side:
  `JWT → Patient → Consultation (patient_id match) → ClinicalHistory`
- `consultation_id` is always taken from the **URL path** — never from the request body.
- A patient cannot access or modify another patient's clinical history (returns `HTTP 404`).

| Method | Endpoint | Auth Required | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/consultations/{id}/history` | Bearer JWT (Patient) | Create clinical history for a consultation |
| `GET` | `/api/v1/consultations/{id}/history` | Bearer JWT (Patient) | Retrieve clinical history |
| `PUT` | `/api/v1/consultations/{id}/history` | Bearer JWT (Patient) | Partially update clinical history |

### Clinical History Fields
All fields are optional (Text / nullable) and correspond directly to the `ClinicalHistory` database model:

| Field | Type | Description |
| :--- | :--- | :--- |
| `chief_complaint` | Text \| null | Primary reason for the visit |
| `history_of_present_illness` | Text \| null | Detailed description of the current illness |
| `past_medical_history` | Text \| null | Previous illnesses and diagnoses |
| `past_surgical_history` | Text \| null | Previous surgical procedures |
| `drug_history` | Text \| null | Current and recent medications |
| `allergy_history` | Text \| null | Known drug and non-drug allergies |
| `family_history` | Text \| null | Relevant family medical history |
| `personal_history` | Text \| null | Lifestyle, occupation, habits |
| `review_of_systems` | Text \| null | Systematic organ-by-organ review |

### 1:1 Constraint
A consultation supports **exactly one** clinical history record.
Attempting to create a second history for the same consultation returns `HTTP 409`.

### POST /api/v1/consultations/{id}/history
```bash
curl -X POST "http://localhost:8000/api/v1/consultations/{consultation_id}/history" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "chief_complaint": "Chest pain on exertion",
    "history_of_present_illness": "Started 2 weeks ago, worsens on climbing stairs.",
    "past_medical_history": "Hypertension since 2015",
    "drug_history": "Amlodipine 5mg OD",
    "allergy_history": "NKDA"
  }'
```

**Example Response (HTTP 201):**
```json
{
  "id": "b2c3d4e5-...",
  "consultation_id": "a1b2c3d4-...",
  "chief_complaint": "Chest pain on exertion",
  "history_of_present_illness": "Started 2 weeks ago, worsens on climbing stairs.",
  "past_medical_history": "Hypertension since 2015",
  "past_surgical_history": null,
  "drug_history": "Amlodipine 5mg OD",
  "allergy_history": "NKDA",
  "family_history": null,
  "personal_history": null,
  "review_of_systems": null,
  "created_at": "2026-09-05T11:00:00Z",
  "updated_at": "2026-09-05T11:00:00Z"
}
```

### GET /api/v1/consultations/{id}/history
```bash
curl -X GET "http://localhost:8000/api/v1/consultations/{consultation_id}/history" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>"
```

### PUT /api/v1/consultations/{id}/history
Only provided fields are updated — omitted fields retain their current values.
The clinical history must already exist (use POST to create it first).

```bash
curl -X PUT "http://localhost:8000/api/v1/consultations/{consultation_id}/history" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "drug_history": "Amlodipine 5mg OD, Atorvastatin 40mg OD",
    "review_of_systems": "Mild dyspnea on exertion, no syncope, no ankle swelling"
  }'
```

### Error Responses
| HTTP Code | Scenario |
| :--- | :--- |
| `401` | Missing or invalid Bearer token |
| `404` | Consultation not found, belongs to another patient, or no clinical history exists |
| `409` | A clinical history already exists for this consultation (duplicate POST) |

---

## 14. Implemented Steps (Updated)

| Step | Feature | Status |
| :--- | :--- | :--- |
| Step 1 | Authentication (Patient + Hospital, JWT, bcrypt) | ✅ Complete |
| Step 2 | Patient Profile + Consultation Management | ✅ Complete |
| Step 3 | Clinical History Foundation | ✅ Complete |
| Step 4 | AI Clinical History Interview Foundation | ✅ Complete |
| Step 5 | Document Upload (OCR) | 🔜 Not started |
| Step 6 | Timeline & Summary | 🔜 Not started |
| Step 7 | Hospital Review Dashboard | 🔜 Not started |

> Production LLM integration, speech-to-text, OCR document processing, and ABDM integration are **next stages**.

---

## 15. AI Clinical History Interview Foundation (Step 4)

Step 4 implements the backend session and message infrastructure for an AI-assisted clinical interview.

### Architecture

```
Patient → Consultation → AI Session → AI Messages → Structured Clinical History
```

### Security & Ownership Chain
- All endpoints require a valid `Bearer` JWT for an authenticated **patient** account.
- The ownership chain is strictly enforced server-side:
  `JWT → Patient → Consultation (patient_id match) → AISession → AIMessages`
- `consultation_id` and `session_id` are derived exclusively from the **URL path** — never from request bodies.
- Cross-patient access attempts return `HTTP 404` to avoid leaking the existence of other patients' sessions or messages.
- Role/sender spoofing is prevented: clients calling the message endpoint are fixed server-side to `sender="patient"`. Attempts to pass `sender="ai"` or `role="assistant"` are rejected with `HTTP 422`.

### Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/consultations/{consultation_id}/ai-sessions` | Create a new AI interview session for a consultation |
| `GET` | `/api/v1/ai-sessions/{session_id}` | Retrieve AI session details (ownership verified) |
| `POST` | `/api/v1/ai-sessions/{session_id}/complete` | Mark session as completed (sets `completed_at`, 409 if terminal) |
| `POST` | `/api/v1/ai-sessions/{session_id}/messages` | Add a patient message (transitions state to `in_progress`, 409 if completed) |
| `GET` | `/api/v1/ai-sessions/{session_id}/messages` | List session messages in strict chronological order (paginated) |

### AISession Status State Machine
```
[initiated] ──(first message sent)──> [in_progress] ──(complete called)──> [completed]
```
Attempting to add messages to or complete a session already in a terminal state returns `HTTP 409 Conflict`.

---

## Step 5A — AI Provider Architecture

Clinova uses a **provider-independent AI abstraction layer**. No single AI model is hard-coded. Different clinical tasks can route to different providers, and switching providers requires only a configuration change — no code changes.

### Architecture Overview

```
         Clinical Services (ai_interview_service, etc.)
                          ↓
                    AITaskRouter           (app/ai/router.py)
                          ↓
               AIProvider Interface        (app/ai/providers/base.py)
                          ↓
       ┌──────────────────┼──────────────────┐
       ↓                  ↓                  ↓
 GeminiProvider    OpenAIProvider     OllamaProvider
  (gemini.py)       (openai.py)       (ollama.py)
```

**Key design principles:**
- Provider SDK imports (`google.genai`, `openai`) are **confined inside adapter modules** — they never leak into API endpoints, schemas, models, or services.
- Providers are **lazily initialised** — no network calls at startup.
- Missing API keys do **not** crash the application at startup.
- The application communicates only with `AIProvider` — never with provider-specific SDK objects.

### Package Structure

```
backend/app/ai/
├── __init__.py          # Public exports
├── config.py            # AIConfig — pydantic-settings for all provider vars
├── schemas.py           # AIRequest, AIResponse, AIProviderError, AIErrorKind
├── tasks.py             # AITaskType enum
├── registry.py          # get_provider() factory with instance caching
├── router.py            # AITaskRouter — task→provider with fallback
└── providers/
    ├── __init__.py
    ├── base.py          # AIProvider abstract base class
    ├── gemini.py        # Google Gemini adapter
    ├── openai.py        # OpenAI adapter (also: Groq, OpenRouter, Cerebras)
    └── ollama.py        # Ollama local adapter (httpx, no extra SDK)
```

### AI Task Types

| Task | Enum Value | Description |
|------|-----------|-------------|
| Clinical History Interview | `HISTORY_INTERVIEW` | Conversational AI intake |
| Structured Extraction | `STRUCTURED_EXTRACTION` | Extract clinical data as JSON |
| Clinical Summary | `CLINICAL_SUMMARY` | Generate readable summaries |
| Document Analysis | `DOCUMENT_ANALYSIS` | Analyse medical documents |
| Translation | `TRANSLATION` | Translate clinical content |
| Triage | `TRIAGE` | Preliminary severity assessment |

> **Note:** Task types are routing definitions only. Clinical AI capabilities are implemented in future steps.

### Environment Variables (Step 5A)

Add these to your `.env` file:

```env
# Provider selection
AI_DEFAULT_PROVIDER=ollama          # gemini | openai | ollama | groq | openrouter

# Per-task overrides (optional — comment out to use AI_DEFAULT_PROVIDER)
# AI_HISTORY_INTERVIEW_PROVIDER=gemini
# AI_STRUCTURED_EXTRACTION_PROVIDER=openai
# AI_CLINICAL_SUMMARY_PROVIDER=gemini

# Fallback chain (comma-separated, tried in order after primary fails)
# AI_FALLBACK_PROVIDERS=ollama,openai

# Google Gemini
# GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.0-flash

# OpenAI
# OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini

# Groq (OpenAI-compatible)
# GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# OpenRouter
# OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=openai/gpt-4o-mini

# Ollama (local, no API key)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

### Provider Configuration Details

#### Ollama (Local — Recommended for Development)

Ollama runs locally with no API key and no cost:

```bash
# Install: https://ollama.ai
ollama pull llama3.2     # download model (~2GB)
ollama serve             # start server (default: localhost:11434)
```

Set in `.env`:
```env
AI_DEFAULT_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

Ollama is **not contacted at startup** — only when a request is made.

#### Google Gemini

```env
AI_DEFAULT_PROVIDER=gemini
GEMINI_API_KEY=your_api_key_from_aistudio
GEMINI_MODEL=gemini-2.0-flash
```

Get your key: [Google AI Studio](https://aistudio.google.com/app/apikey)

#### OpenAI

```env
AI_DEFAULT_PROVIDER=openai
OPENAI_API_KEY=your_key_from_platform_openai
OPENAI_MODEL=gpt-4o-mini
```

#### Groq (Fast, Free Tier Available)

```env
AI_DEFAULT_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
```

Groq uses the `OpenAIProvider` adapter internally with Groq's base URL.

#### OpenRouter (Access Many Models via One API)

```env
AI_DEFAULT_PROVIDER=openrouter
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=openai/gpt-4o-mini
```

### Task Routing

Configure which provider handles each task:

```env
# Route different tasks to different providers
AI_HISTORY_INTERVIEW_PROVIDER=gemini        # conversational
AI_STRUCTURED_EXTRACTION_PROVIDER=openai   # reliable JSON
AI_TRIAGE_PROVIDER=gemini                  # most capable
AI_TRANSLATION_PROVIDER=ollama             # local/private
```

### Fallback Mechanism

The `AITaskRouter` implements a bounded fallback chain:

```
Primary Provider  ──(fail: retryable)──→  Fallback 1  ──(fail)──→  Fallback 2
                                                                         ↓
                                                              AIProviderError (surfaced)
```

**Error categories:**

| Kind | Retryable | Description |
|------|-----------|-------------|
| `AUTH_ERROR` | ❌ No | Missing/invalid API key — operator action required |
| `INVALID_REQUEST` | ❌ No | Bad request — fix the request |
| `PROVIDER_UNAVAILABLE` | ✅ Yes | Endpoint down/unreachable |
| `RATE_LIMIT` | ✅ Yes | Quota exhausted — try another provider |
| `TIMEOUT` | ✅ Yes | Request timed out |
| `MALFORMED_RESPONSE` | ✅ Yes | Provider returned unexpected format |
| `UNEXPECTED_ERROR` | ✅ Yes | Catch-all |

Configure fallbacks:
```env
AI_FALLBACK_PROVIDERS=ollama,openai
```

Maximum 3 total attempts (bounded — never infinite retry).

### Adding a New Provider

1. Create `backend/app/ai/providers/yourprovider.py` — subclass `AIProvider`, implement `generate()`.
2. Register it in `backend/app/ai/registry.py` — add to `_KNOWN_PROVIDERS` and `_create_provider()`.
3. Add config fields to `backend/app/ai/config.py` (API key, model, base URL).
4. Document in `.env.example`.

No other files need to change. The application immediately supports `AI_DEFAULT_PROVIDER=yourprovider`.

### Security Notes

- API keys are **never logged**, **never returned** in API responses, **never placed in JWT tokens**.
- Provider SDK objects never reach API endpoints or clinical schemas.
- Ollama/provider endpoints are never exposed to the frontend — all AI calls go through the Clinova backend.
- Clinical conversation content is not logged at the provider level.

