# Clinova SIH Live Demonstration Runbook

## 1. Overview & Demonstration Objective
This runbook provides the exact, turn-by-turn operational guide for presenting the **Clinova Intelligent Clinical Intake & Triage Platform** to the Smart India Hackathon (SIH) evaluation jury.

The demonstration proves the **unbroken patient-to-physician workflow**:
$$\text{Patient (Web / Mobile)} \to \text{Identify (ABHA)} \to \text{Consent} \to \text{Language} \to \text{Adaptive Intake} \to \text{Triage} \to \text{Timeline} \to \text{Summary} \to \text{Doctor Queue} \to \text{Workspace Review} \to \text{Doctor Confirmation}$$

---

## 2. Infrastructure & Port Mapping

| Service | Technology | Port / URL | Purpose |
| :--- | :--- | :--- | :--- |
| **FastAPI Backend** | Python 3.11+ / FastAPI / Uvicorn | `http://localhost:8000` | Central REST API, AI engine, deterministic triage, auth |
| **Patient Web Portal** | React 19 / TypeScript / Vite | `http://localhost:5173` | Responsive web patient intake experience |
| **Hospital Web Portal** | React 19 / TypeScript / Vite | `http://localhost:5174` | Desktop physician OPD triage queue & workspace |
| **Patient Mobile App** | React Native / Expo SDK 57 | `Expo Go / Android` | Native mobile client with camera scanner & voice input |
| **Relational Store** | PostgreSQL 15+ | `localhost:5432/clinova` | Persistent relational store for all clinical records |

---

## 3. Pre-Demo Setup & Clean Environment Initialization

### Step 3.1: Database Migration & Synthetic Demo Seed
From the backend directory:
```powershell
cd Clinova-sih\backend
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe scripts/demo_seed.py --reset --seed
```
*Expected Output:*
```text
[INFO] Purging synthetic demo data...
[INFO] Demo data reset completed successfully.
[INFO] Created Demo Hospital: Demo General Hospital
[INFO] Created Attending Physician: doctor@demohospital.org
[INFO] Seeded Consultation A: Rohan Patil (Routine / Green)
[INFO] Seeded Consultation B (Red Flag): Ananya Deshmukh (Emergency / Red)
[INFO] All demo records committed successfully!
```

### Step 3.2: Verify Live Backend API Health & Contract
Run the automated pre-flight smoke test:
```powershell
.\.venv\Scripts\python.exe scripts/smoke_test.py
```
*Expected Output:*
```text
[OK] 1. GET /api/v1/health -> 200 OK
[OK] 2. GET /api/v1/health/db -> 200 OK
[OK] 3. POST /api/v1/auth/patient/login -> 200 OK (JWT received)
...
ALL 14 API CONTRACT SMOKE TESTS PASSED CLEANLY ON LIVE DATABASE!
```

---

## 4. Service Launch Commands (Dedicated Terminals)

### Terminal 1: Backend Server (Port 8000)
```powershell
cd Clinova-sih\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*Verify in browser:* `http://localhost:8000/api/v1/health` -> `{"status": "ok"}`

### Terminal 2: Patient Web Portal (Port 5173)
```powershell
cd Clinova-sih\clients\patient-web
npm run dev
```
*URL:* `http://localhost:5173`

### Terminal 3: Hospital Web Portal (Port 5174)
```powershell
cd Clinova-sih\clients\hospital-web
npm run dev
```
*URL:* `http://localhost:5174`

### Terminal 4: Patient Mobile Application (Expo)
```powershell
cd Clinova-sih\clients\patient-mobile
npx expo start
```
- Press `a` for Android emulator (connects automatically to `http://10.0.2.2:8000/api/v1`).
- Or scan QR code in **Expo Go** on a physical Android phone connected to the same Wi-Fi network.

---

## 5. Demonstration Credentials Reference

| Role | Username / Email | Password | Details |
|---|---|---|---|
| **Attending Physician** | `doctor@demohospital.org` | `HospitalPass123!` | Cardiology & General Medicine OPD |
| **Patient A (Routine)** | `rohan.patil@example.com` | `PatientPass123!` | Rohan Patil (34M), ABHA: `91-4521-8890-1234` |
| **Patient B (Emergency)** | `ananya.d@example.com` | `PatientPass123!` | Ananya Deshmukh (45F), ABHA: `91-6789-1122-3344` |

---

## 6. Step-by-Step Jury Presentation Flow

### Scenario 1: Standard Intake & Doctor Review (Patient Rohan Patil)

#### Phase A: Patient Experience (Web `http://localhost:5173` or Mobile)
1. **Landing & Identity**:
   - Sign in using `rohan.patil@example.com` / `PatientPass123!`.
   - Point out verified demographic profile: *Rohan Patil, 34M, ABHA: 91-4521-8890-1234*.
2. **Informed Consent & Safety Boundary**:
   - Show consent confirmation. Explain that Clinova enforces explicit patient consent before AI processing or record retrieval.
   - Point out clear disclaimer: *Assistive AI tool only; all medical decisions remain exclusively with licensed physicians.*
3. **Multilingual Selection**:
   - Point out English, Hindi, and Marathi options.
   - Note the **AYUSH Intake (Phase 2)** badge clearly marked as disabled to respect SIH MVP scope.
4. **Adaptive AI Clinical Intake**:
   - Describe dry cough and evening fever. Show AI follow-up questions clarifying duration and breathing symptoms.
5. **Medical Timeline**:
   - Navigate to `/timeline` displaying chronological, source-attributed events (`28 Aug 2026`, historical `~2021` avoiding fabricated calendar days).
6. **Summary Review & Declaration**:
   - Review AI-generated draft summary with draft badge: *"AI-generated draft pending clinical review."*
   - Check mandatory verification box and click **"Submit to Doctor Queue"**.

#### Phase B: Physician Review & Queue Management (Hospital Web `http://localhost:5174`)
1. **Clinician Authentication**:
   - Log in as Attending Physician: `doctor@demohospital.org` / `HospitalPass123!`.
2. **OPD Triage Queue**:
   - Observe live queue showing active consultations with deterministic priority badges (`ROUTINE` / `GREEN`).
3. **Clinical Workspace**:
   - Open patient consultation.
   - Review AI draft summary, chief complaint, timeline, and source medical documents.
   - Edit/add clinician impression notes.
4. **Doctor Confirmation**:
   - Click **"Confirm & Finalize Summary"**.
   - Consultation status updates to `confirmed`/`reviewed`.

---

### Scenario 2: Deterministic Red-Flag Triage Escalation (Patient Ananya Deshmukh)

1. **Patient Input**:
   - In Patient Web or Mobile AI chat, patient states:
     > *"I have severe crushing chest pain radiating to my left arm and difficulty breathing since 30 minutes."*
2. **Deterministic Triage**:
   - Backend evaluation engine detects high-risk cardiovascular red flags.
   - Assigns priority `EMERGENCY` / `RED`.
3. **Immediate Emergency Response**:
   - Patient UI immediately displays high-visibility emergency modal:
     - Calm, non-diagnostic guidance advising immediate emergency room visit or calling `108`/`112`.
     - Zero local diagnostic speculation or drug prescriptions.
4. **Doctor Queue Escalation**:
   - On Hospital Portal (`http://localhost:5174`), the consultation automatically surfaces to the top of the queue with an urgent **EMERGENCY (RED)** alert banner for immediate clinician triage.
