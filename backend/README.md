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
| Step 5A | Multi-Provider AI Architecture (Gemini/OpenAI/Groq/Ollama) | ✅ Complete |
| Step 5B | Real Adaptive AI Clinical History Interview Engine | ✅ Complete |
| Step 6 | Red-Flag Detection & Emergency Triage Engine | ✅ Complete |
| Step 7 | Physician Summary Generation | 🔜 Not started |
| Step 8 | Document Upload (OCR) | 🔜 Not started |
| Step 9 | Hospital Review Dashboard | 🔜 Not started |

> Production LLM integration, triage alerts, and clinical interview engines are active. OCR document processing, physician summaries, and ABDM integration are next stages.

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
# Primary/default AI provider (cloud AI is normal default; Ollama is last fallback)
AI_DEFAULT_PROVIDER=gemini          # gemini | openai | ollama | groq | openrouter

# Per-task overrides (override AI_DEFAULT_PROVIDER per task)
AI_HISTORY_INTERVIEW_PROVIDER=gemini
AI_STRUCTURED_EXTRACTION_PROVIDER=gemini
AI_CLINICAL_SUMMARY_PROVIDER=gemini
AI_DOCUMENT_ANALYSIS_PROVIDER=gemini
AI_TRANSLATION_PROVIDER=gemini
AI_TRIAGE_PROVIDER=gemini

# Ordered fallback chain (Ollama is intentionally the LAST fallback)
AI_FALLBACK_PROVIDERS=groq,openrouter,ollama

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

# Ollama (local, no API key — last fallback or explicit local dev)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

### Provider Configuration Details

#### Ollama (Local Development / Last-Resort Fallback)

Ollama serves as the final local fallback when cloud providers are unreachable, and can also be used directly for zero-cost, offline local development:

```bash
# Install: https://ollama.ai
ollama pull llama3.2     # download model (~2GB)
ollama serve             # start server (default: localhost:11434)
```

To explicitly use Ollama for local development:
```env
AI_DEFAULT_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

Ollama is **not contacted at startup** — only when an inference request is routed to it.

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
 
The `AITaskRouter` implements a bounded fallback chain ensuring high availability:
 
```
Task-Specific Provider
         ↓ (retryable failure)
Default Provider (Gemini)
         ↓ (retryable failure)
Groq
         ↓ (retryable failure)
OpenRouter
         ↓ (retryable failure)
Ollama (Final Local Fallback)
         ↓ (exhaustion)
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
AI_FALLBACK_PROVIDERS=groq,openrouter,ollama
```
 
Maximum 5 total attempts (bounded — never infinite retry). Ollama is always placed last in the fallback chain unless explicitly selected as the primary provider.

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

---

## 14. Step 5B: Real AI Clinical History Interview Engine

> [!IMPORTANT]
> **Clinical Intake Boundary**: The AI is an information-gathering assistant ONLY.
> It assists with clinical history collection and **DOES NOT provide diagnosis or treatment**.
> All collected information is reviewed and confirmed by licensed physicians.

### Architectural Overview

```
Patient Client
     │  (POST /api/v1/ai-sessions/{session_id}/messages)
     ▼
FastAPI Route & Dependency Layer
     │  (Verify JWT identity, verify consultation & session ownership)
     ▼
AI Message Service
     │  (Persist patient message with sender="patient", transition to "in_progress")
     ▼
AI Interview Service (Real Adaptive Engine)
     ├── 1. Build bounded conversation context (chronological)
     ├── 2. Fetch current ClinicalHistory & derive InterviewState
     ├── 3. Assemble safety-constrained system prompt + language
     ├── 4. AITaskRouter (HISTORY_INTERVIEW) → AIProvider (Gemini/OpenAI/Ollama)
     ├── 5. Pydantic parser & validation layer (ClinicalInterviewAIResponse)
     ├── 6. Safe merge into ClinicalHistory (no overwriting existing data with null)
     ├── 7. Server-controlled AI Message saved (sender="ai")
     └── 8. Check completion criteria (core sections required)
     ▼
Enriched Backward-Compatible Response (AIInterviewMessageResponse)
```

### Key Components

1. **Safety Constraints**:
   - Explicit instructions in `app/ai/prompts/clinical_history.py` forbidding diagnosis, prescription, medical certainty, or fact fabrication.
   - Uncertain patient statements are recorded as unconfirmed, self-reported concerns.
   - The AI asks ONE focused question at a time.
   - No diagnostic or medication fields exist in `ExtractedClinicalInfo`.

2. **Full Conversation Context**:
   - `build_conversation_context` loads recent messages chronologically (sender translated: `patient` → `user`, `ai` → `assistant`).
   - Configurable bounded window via `AI_INTERVIEW_MAX_HISTORY_MESSAGES` (default: 20).
   - Session isolation guarantees that messages from other patients are never retrieved or passed to the model.

3. **Runtime Interview State**:
   - `derive_interview_state` computes completed vs. missing sections purely from current `ClinicalHistory` without extra database tables.
   - Priority section order: Chief Complaint → HPI → Past Medical → Past Surgical → Drug → Allergy → Family → Personal → Review of Systems.

4. **Structured AI Response**:
   - Schema defined in `app/ai/interview/schemas.py`:
     ```json
     {
       "next_question": "When did your headache start?",
       "extracted_information": {
         "chief_complaint": "Headache",
         "history_of_present_illness": "Frontal headache for 2 days"
       },
       "missing_information": ["severity", "associated nausea"],
       "current_section": "history_of_present_illness",
       "section_complete": false,
       "interview_complete": false
     }
     ```
   - Only non-None, patient-supported fields are updated into `ClinicalHistory`.

5. **Multilingual Support**:
   - Built-in instruction prompts for **English**, **Hindi**, and **Marathi**, driven by `AISession.language`.

6. **Feature Flagging & Controlled Fallback**:
   - `AI_INTERVIEW_ENABLED=true`: enables real LLM inference via the task router.
   - `AI_INTERVIEW_ENABLED=false`: uses safe, conversational placeholder follow-up without invoking external providers.
   - If all providers fail: the service catches `AIProviderError`, logs the failure safely, preserves the patient message, does not corrupt clinical history, and returns a safe fallback question.

### Configuration

Add to `.env`:
```env
# Step 5B Settings
AI_INTERVIEW_ENABLED=true
AI_INTERVIEW_MAX_HISTORY_MESSAGES=20
```

### Running Tests

```powershell
# Run the Step 5B interview engine tests
.\.venv\Scripts\python.exe -m pytest tests/test_ai_interview.py -v

# Run the complete test suite (all steps)
.\.venv\Scripts\python.exe -m pytest -v
```

### Current Limitations (Deferred to Future Steps)
- Physician summary generation (Step 7)
- Document Upload & OCR (Step 8)
- Hospital Review Dashboard (Step 9)
- ABDM / FHIR data export
- Voice input / speech-to-text / text-to-speech
- Web frontend UI integration

---

## 16. Step 6: Red-Flag Detection & Emergency Triage Engine

> [!IMPORTANT]
> **Clinical Safety Boundary**: Red-flag detection is a **clinical safety-support feature, NOT a diagnostic system**.
> It NEVER provides medical diagnoses (e.g., "You have a heart attack" or "You have appendicitis") and NEVER provides medication or home treatment instructions.
> Its sole clinical functions are:
> 1. Rapidly flagging urgent/emergency clinical presentations for hospital staff attention.
> 2. Returning a calm, non-alarming safety notice directing patients to seek immediate medical care when emergencies are detected.
> 3. Creating structured, persistent hospital triage alerts in PostgreSQL.

### Architecture & Safety Flow

Clinova employs a **deterministic-authoritative triage model** where rules are the final authority and cannot be bypassed or downgraded by AI inference:

```
Patient Message / Clinical Intake
             │
             ▼
     Optional AI Extraction
     (Task: AITaskType.TRIAGE)
     • Extracts clinical findings & quotes
     • Bounded by provider timeout/circuit breaker
     • AI cannot override or downgrade deterministic rules
             │
             ▼
 Authoritative Deterministic Rule Engine
 (DeterministicTriageDetector)
     • Evaluates extracted evidence + raw message + clinical history
     • Context-aware negation filtering ("no chest pain", "rules out shortness of breath")
     • Evaluates 9 high-risk clinical categories:
       - 1. Cardiovascular / Chest Pain
       - 2. Respiratory / Breathing Distress
       - 3. Neurological / Stroke / Deficits
       - 4. Severe / Uncontrolled Bleeding
       - 5. Acute Severe Abdominal Pain
       - 6. Anaphylaxis / Severe Allergic Reactions
       - 7. Altered Mental Status / Syncope
       - 8. Immediate Self-Harm / Suicide Risk
       - 9. High-Risk Obstetric / Pregnancy Complications
             │
             ▼
     Structured TriageResult
     (Urgency: NORMAL | URGENT | EMERGENCY_REVIEW)
             │
             ├─────────────────────────────────────────────────┐
             ▼                                                 ▼
 Post-Interview Response Guard                     PostgreSQL Alerts Store
 • If EMERGENCY_REVIEW:                            • Synchronizes alerts to `alerts` table
   Replaces AI message with calm safety notice:     • Deduplication by (consultation_id, alert_type)
   "Some of the symptoms you reported may need      • Real-time visibility for hospital triage desk
    urgent medical attention. Please inform the
    hospital triage staff immediately or proceed
    to the nearest emergency department."
 • If NORMAL / URGENT:
   Interview continues normal clinical inquiry
```

### High-Priority Red-Flag Categories

| Category | Typical Indicators | Urgency Level | Recommended Clinical Action |
| :--- | :--- | :--- | :--- |
| **Cardiovascular** | Crushing/radiating chest pain, pressure with sweating | `EMERGENCY_REVIEW` | Immediate triage evaluation & ECG |
| **Respiratory** | Severe breathlessness, gasping, stridor, cyanosis | `EMERGENCY_REVIEW` | Immediate airway & oxygenation assessment |
| **Neurological** | Facial droop, arm weakness, slurred speech, sudden confusion | `EMERGENCY_REVIEW` | Immediate stroke protocol activation |
| **Hemorrhage** | Vomiting blood, coughing blood, black tarry stools | `EMERGENCY_REVIEW` | Immediate hemodynamic & hemorrhage review |
| **Acute Abdomen** | Sudden severe rigid abdominal pain with fever/vomiting | `EMERGENCY_REVIEW` / `URGENT` | Urgent surgical / abdominal evaluation |
| **Anaphylaxis** | Swelling of lips/tongue/throat with breathing difficulty | `EMERGENCY_REVIEW` | Immediate emergency resuscitation review |
| **Consciousness** | Syncope, loss of consciousness, unresponsiveness | `EMERGENCY_REVIEW` | Immediate vital signs & neurological triage |
| **Self-Harm** | Active suicidal intent or self-harm statements | `EMERGENCY_REVIEW` | Immediate crisis intervention & safety escort |
| **Obstetric** | Heavy vaginal bleeding, severe pain in pregnancy | `EMERGENCY_REVIEW` | Immediate obstetric emergency review |

### Offline & Fallback Resilience
- **Zero AI Dependency**: The triage system works completely even if all AI providers are offline or misconfigured. In offline mode, the deterministic regex engine evaluates the raw text directly and maintains 100% emergency detection sensitivity.
- **Provider Fallback**: When AI is enabled, the triage task follows the same router chain (`Gemini` → `OpenAI` → `Groq` → `OpenRouter` → `Ollama`), guaranteeing that Ollama is only used as a final local fallback.

### Available Triage Endpoints

| Method | Endpoint | Auth Required | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/consultations/{id}/triage` | Bearer JWT (Patient or Hospital) | Run full triage assessment on current consultation history & messages |
| `GET` | `/api/v1/consultations/{id}/alerts` | Bearer JWT (Patient or Hospital) | Retrieve active triage alerts generated for this consultation |

#### Access Control & Security
- **Patient Isolation**: Patients can only inspect triage status and alerts for their own consultations. Requesting another patient's consultation returns `HTTP 404 Not Found` (never leaking consultation existence).
- **Hospital Clinical Review**: Authorized doctors, hospital admins, and clinical staff can access triage results and alerts for consultations belonging to their assigned hospital.

### Example Responses

#### GET /api/v1/consultations/{id}/triage
```json
{
  "consultation_id": "a1b2c3d4-...",
  "urgency": "EMERGENCY_REVIEW",
  "has_red_flags": true,
  "findings": [
    {
      "category": "cardiovascular",
      "severity": "CRITICAL",
      "rule_id": "CHEST_PAIN_CRUSHING",
      "title": "Severe/Crushing Chest Pain",
      "description": "Patient reports severe crushing chest pain radiating to left arm",
      "patient_quote": "crushing chest pain radiating to my left arm",
      "requires_emergency": true
    }
  ],
  "recommended_action": "Patient requires immediate in-person clinical evaluation.",
  "safety_notice": "Some of the symptoms you reported may need urgent medical attention. Please inform the hospital triage staff immediately or proceed to the nearest emergency department.",
  "evaluated_at": "2026-09-06T09:00:00Z"
}
```

#### GET /api/v1/consultations/{id}/alerts
```json
{
  "items": [
    {
      "id": "e5f6g7h8-...",
      "consultation_id": "a1b2c3d4-...",
      "patient_id": "4ab93c21-...",
      "alert_type": "red_flag_cardiovascular",
      "severity": "high",
      "message": "Patient reports severe crushing chest pain radiating to left arm",
      "source": "triage_engine",
      "status": "active",
      "created_at": "2026-09-06T09:00:00Z",
      "updated_at": "2026-09-06T09:00:00Z",
      "acknowledged_at": null
    }
  ],
  "total": 1,
  "consultation_id": "a1b2c3d4-..."
}
```

### Running Triage Tests

```powershell
# Run only Step 6 triage tests
.\.venv\Scripts\python.exe -m pytest tests/test_triage.py -v

# Run the complete test suite
.\.venv\Scripts\python.exe -m pytest -v
```



