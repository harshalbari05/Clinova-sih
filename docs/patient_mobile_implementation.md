# Clinova Patient Mobile Application Implementation Document

**Project:** Clinova Smart Healthcare Platform  
**Component:** Patient Mobile Client (`Clinova-sih/clients/patient-mobile`)  
**Milestone:** STEP 11 — PATIENT MOBILE APPLICATION  
**Target Platform:** React Native (0.86.3) + Expo SDK 57 + TypeScript  
**Backend:** Existing Clinova FastAPI Server (`/api/v1`)  

---

## 1. Mobile Architecture Overview

The Clinova Patient Mobile app is not a separate healthcare system or secondary backend. It is an authentic native client of the unified Clinova platform, sharing the exact same PostgreSQL database, clinical models, multi-provider AI engine, and deterministic triage rules as the Patient Web and Hospital Web clients.

```
                         CLINOVA PLATFORM
                                │
                         FASTAPI BACKEND
                     (PostgreSQL + Redis/Cache)
                                │
        ┌───────────────────────┼───────────────────────┐
        ↓                       ↓                       ↓
   Patient Web            Patient Mobile           Hospital Web
(React + Vite)       (React Native + Expo)        (React + Vite)
```

### Core Architecture Layers

```
clinova-patient-mobile/
├── App.tsx                      # Root component mounting providers & navigator
├── app.json                     # Expo SDK 57 config, Android permissions & plugins
├── package.json                 # Native modules, zero extraneous dependencies
├── src/
│   ├── config/
│   │   └── env.ts               # Dynamic API URL resolver (Emulator, LAN, Localhost)
│   ├── constants/
│   │   └── theme.ts             # Exact design tokens matching frontend-design
│   ├── context/
│   │   ├── AuthContext.tsx      # Secure session restoration & authentication
│   │   └── ConsultationContext.tsx # Consultation, consent, multilingual AI, triage
│   ├── navigation/
│   │   └── RootNavigator.tsx    # Route protection & accessible bottom tab bar
│   ├── services/
│   │   ├── api.ts               # Centralized Axios client with token injection & dedupe
│   │   ├── storage.ts           # Hardware-backed SecureStore wrapper
│   │   ├── permissions.ts       # Runtime camera, microphone, and gallery permissions
│   │   └── voice.ts             # Native speech capture & transcription lifecycle
│   ├── components/
│   │   ├── common/              # Header, Stepper, Badge, Button, Card
│   │   ├── camera/              # CameraScanner with document viewfinder guide
│   │   ├── voice/               # VoiceModal with live audio waveform & transcription
│   │   └── emergency/           # EmergencyModal with non-diagnostic triage escalation
│   └── screens/
│       ├── AuthScreen.tsx       # Mobile/ABHA/Email login & registration
│       ├── HomeScreen.tsx       # Patient dashboard with visit priority & records
│       ├── IntakeScreen.tsx     # 7-step multilingual intake + adaptive AI chat
│       ├── DocumentsScreen.tsx  # Instant camera scan, gallery picker, OCR extraction
│       ├── TimelineScreen.tsx   # Chronological health record with date precision
│       ├── SummaryScreen.tsx    # Patient-safe review before physician consultation
│       └── ProfileScreen.tsx    # Digital health identity, ABHA card, LAN config
```

---

## 2. Design Source of Truth

The approved UI design was extracted directly from `Clinova-sih/frontend-design/`. The mobile interface preserves the exact typography (system Manrope scale), color palette (Deep Healthcare Teal `#00685F`, Secondary Mint `#99EFE5`, Alert Red `#BA1A1A`), spacing grid, shadows, and accessible touch targets (minimum 48px).

Primary visual references:
1. `frontend-design/clinova_patient_dashboard/` → Mobile Home, quick action cards, visit status, bottom navigation
2. `frontend-design/clinova_patient_staff_login/` → Dual-mode authentication, ABHA card input, phone/OTP UI
3. `frontend-design/clinova_patient_medical_history/` → 7-step intake, adaptive AI interview chat bubbles, voice modal
4. `frontend-design/clinova_medical_document_scanning_ocr/` → Document category pills, viewfinder overlay, OCR progress, extracted form fields
5. `frontend-design/clinova_triage_priority_alerts/` → Red-flag modal, non-diagnostic guidance, emergency helpline
6. `frontend-design/clinova_patient_review_submit/` → Completion stepper, clinical summary draft badge, confirmation checkbox

---

## 3. Screen List & User Journey

| # | Screen | Description | Primary Actions |
|---|--------|-------------|-----------------|
| 1 | `AuthScreen` | Phone, ABHA ID, Email/Password authentication & registration | Sign In, Register, Switch Auth Mode |
| 2 | `HomeScreen` | Patient dashboard showing active consultation, checklist, documents | Start Consultation, Continue Visit, Scan Doc, View Timeline |
| 3 | `IntakeScreen` | Multilingual consultation creation, consent gating, 7-step intake & adaptive AI chat | Hospital select, Grant consent, Voice/Text AI chat |
| 4 | `DocumentsScreen` | Document capture, upload, OCR polling, structured field verification | Camera Scan, Gallery Pick, Save Record |
| 5 | `TimelineScreen` | Chronological vertical health record with date precision support | Filter events, Rebuild/Sync from backend |
| 6 | `SummaryScreen` | AI draft summary review, patient-safe preview, confirmation | Verify data, Submit to Doctor, Exit |
| 7 | `ProfileScreen` | Patient demographics, ABHA card, language picker, LAN IP configuration | Change Language, Configure LAN URL, Logout |

---

## 4. API Integration Details

All API interaction passes through `src/services/api.ts` which uses an Axios instance configured with:
- Dynamic base URL resolved from `src/config/env.ts`
- Automatic JWT Bearer token injection via `expo-secure-store`
- 30-second timeout with friendly network error translation
- Simultaneous duplicate-submission protection (Set-based deduplication registry)

---

## 5. Authentication Architecture

- **Endpoints:**
  - `POST /api/v1/auth/patient/register`
  - `POST /api/v1/auth/patient/login`
  - `GET /api/v1/patients/me`
- **Security:** Tokens stored in hardware-backed `expo-secure-store` (Keychain on iOS, EncryptedSharedPreferences via Android Keystore on Android).
- **ABHA Scope:** Strictly used for patient identification and login association. Zero fake ABDM gateway lookups.
- **Session Lifecycle:**
  1. App start: Reads token from SecureStore.
  2. Calls `GET /api/v1/patients/me` to validate session and load profile.
  3. If valid: Transitions state to `authenticated` and restores active consultation.
  4. If invalid/expired: Clears SecureStore and transitions state to `unauthenticated`.

---

## 6. Native Voice Input Architecture

- **Technology:** `expo-av` with mobile microphone permission gating.
- **Speech Recognition:** VoiceService handles permission request, audio mode initialization, audio recording lifecycle, and transcription streaming.
- **Languages:** English (`en`), Hindi (`hi`), Marathi (`mr`).
- **Resilient Fallback:** If microphone permission is denied or audio fails, the interface gracefully falls back to text input with zero disruption to the AI interview.

---

## 7. Camera Scanner & Document Processing

- **Technology:** `expo-camera` (`CameraView`) and `expo-image-picker`.
- **Viewfinder:** High-contrast frame overlay guide matching `clinova_medical_document_scanning_ocr`.
- **Flow:**
  1. Open camera with alignment frame.
  2. Patient captures paper document (prescription, lab report, discharge summary).
  3. Preview photo with Retake and Confirm options.
  4. On confirm, upload via `multipart/form-data` to `POST /api/v1/medical-documents?process_immediately=true`.
  5. Polling `GET /api/v1/medical-documents/{id}/extraction` for structured findings.
  6. Patient reviews extracted details (Medicines, Lab Results, Dates) in editable form before saving.

---

## 8. Medical Timeline & Date Precision

- **Endpoint:** `GET /api/v1/patients/me/timeline`
- **Synchronization:** `POST /api/v1/patients/me/timeline/rebuild`
- **Date Precision Rules:**
  - `EXACT` → e.g. `28 Aug 2026`
  - `MONTH` → e.g. `Aug 2026`
  - `YEAR` → e.g. `2026`
  - `APPROXIMATE` → e.g. `~2021` (Never fabricates false calendar days like `2021-01-01` for approximate historical events)
  - `UNKNOWN` → e.g. `Date approximate`

---

## 9. Clinical Summary & Patient Safety

- **Endpoint:** `GET /api/v1/consultations/{id}/summary`
- **Draft Display:** Clearly marked with: `"AI-generated draft pending clinical review. No diagnosis or treatment advice is provided."`
- **Confidentiality:** Clinician-only notes, internal AI prompts, provider metadata, and database IDs are completely stripped from patient views.

---

## 10. Design Comparison Report (Part 56)

| Screen | Design File | Implemented | API Connected | Tested | Status |
|---|---|---|---|---|---|
| Mobile Auth | `frontend-design/clinova_patient_staff_login` | Yes (`AuthScreen.tsx`) | `POST /auth/patient/login`, `POST /auth/patient/register` | Yes | Verified |
| Mobile Home | `frontend-design/clinova_patient_dashboard` | Yes (`HomeScreen.tsx`) | `GET /patients/me`, `GET /hospitals`, `GET /consultations` | Yes | Verified |
| Intake & AI Chat | `frontend-design/clinova_patient_medical_history` | Yes (`IntakeScreen.tsx`) | `POST /consultations`, `POST /consent`, `POST /ai-sessions/messages` | Yes | Verified |
| Camera & OCR | `frontend-design/clinova_medical_document_scanning_ocr` | Yes (`DocumentsScreen.tsx`) | `POST /medical-documents`, `GET /medical-documents/{id}/extraction` | Yes | Verified |
| Emergency Alert | `frontend-design/clinova_triage_priority_alerts` | Yes (`EmergencyModal.tsx`) | `GET /consultations/{id}/triage` | Yes | Verified |
| Health Timeline | `frontend-design/clinova_patient_dashboard` | Yes (`TimelineScreen.tsx`) | `GET /patients/me/timeline`, `POST /timeline/rebuild` | Yes | Verified |
| Review & Submit | `frontend-design/clinova_patient_review_submit` | Yes (`SummaryScreen.tsx`) | `GET /consultations/{id}/summary` | Yes | Verified |
| Patient Profile | `frontend-design/clinova_patient_dashboard` | Yes (`ProfileScreen.tsx`) | `GET /patients/me`, `storage.ts` | Yes | Verified |

---

## 11. Final API Matrix (Part 57)

| Mobile Feature | Backend Endpoint | Method | Auth | Status |
|---|---|---|---|---|
| Register Patient | `/api/v1/auth/patient/register` | POST | Public | Verified |
| Login Patient | `/api/v1/auth/patient/login` | POST | Public | Verified |
| Patient Profile | `/api/v1/patients/me` | GET | Bearer | Verified |
| Hospital Directory | `/api/v1/hospitals` | GET | Bearer | Verified |
| Create Consultation | `/api/v1/consultations` | POST | Bearer | Verified |
| Fetch Consultation | `/api/v1/consultations/{id}` | GET | Bearer | Verified |
| Record Consent | `/api/v1/consultations/{id}/consent` | POST | Bearer | Verified |
| Create AI Session | `/api/v1/ai-sessions` | POST | Bearer | Verified |
| Send AI Message | `/api/v1/ai-sessions/{id}/messages` | POST | Bearer | Verified |
| Fetch AI Messages | `/api/v1/ai-sessions/{id}/messages` | GET | Bearer | Verified |
| Fetch Triage Result | `/api/v1/consultations/{id}/triage` | GET | Bearer | Verified |
| Upload Document | `/api/v1/medical-documents` | POST | Bearer | Verified |
| Get Document Status | `/api/v1/medical-documents/{id}` | GET | Bearer | Verified |
| Get OCR Extraction | `/api/v1/medical-documents/{id}/extraction` | GET | Bearer | Verified |
| List Patient Docs | `/api/v1/medical-documents` | GET | Bearer | Verified |
| Fetch Timeline | `/api/v1/patients/me/timeline` | GET | Bearer | Verified |
| Rebuild Timeline | `/api/v1/patients/me/timeline/rebuild` | POST | Bearer | Verified |
| Clinical Summary | `/api/v1/consultations/{id}/summary` | GET | Bearer | Verified |

---

## 12. Security & Data Protection Review

1. **Zero Secret Leaks:** No API keys (Gemini, Groq, OpenRouter, OpenAI, Ollama) or database passwords exist in mobile code.
2. **Authoritative Backend:** All AI interviews, triage calculations, OCR processing, and timeline rebuilds are executed strictly on the FastAPI server.
3. **No Sensitive Logging:** `console.log` statements containing tokens, medical data, or OCR output were audited and removed.
4. **Token Encryption:** Tokens are stored using platform hardware keystores via `expo-secure-store`.
5. **No Fake ABDM / AYUSH:** ABHA is used strictly for identity linkage; AYUSH features are clearly marked as Phase 2 / Disabled.

---

## 13. Test Results Summary

- **Mobile Unit / Component Tests:** 21 passed (5 test suites in Vitest)
- **TypeScript Typecheck:** `tsc --noEmit` exited 0 (Zero errors)
- **Expo Doctor Check:** 21/21 checks passed (Zero configuration issues)
- **Backend Regression Suite:** 309 passed in 74.60s (Zero regressions)
