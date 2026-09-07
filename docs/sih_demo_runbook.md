# Clinova SIH Live Demonstration Runbook

## 1. Overview & Demonstration Objective
This runbook provides the exact, turn-by-turn operational guide for presenting the **Clinova Intelligent Clinical Intake & Triage Platform** to the Smart India Hackathon (SIH) evaluation jury.

The demonstration proves the **unbroken patient-to-physician workflow**:
$$\text{Patient Landing} \to \text{Identify} \to \text{Consent} \to \text{Language} \to \text{Adaptive Intake} \to \text{Triage} \to \text{Timeline} \to \text{Summary} \to \text{Doctor Queue} \to \text{Workspace Review} \to \text{Doctor Confirmation}$$

---

## 2. Infrastructure & Port Mapping

| Service | Technology | Port / URL | Purpose |
| :--- | :--- | :--- | :--- |
| **FastAPI Backend** | Python 3.14 / FastAPI / Uvicorn | `http://localhost:8000` | REST API, AI engine, deterministic triage, auth |
| **Patient Web Portal** | React 18 / TypeScript / Vite | `http://localhost:5173` | Mobile-optimized patient intake experience |
| **Hospital Web Portal** | React 18 / TypeScript / Vite | `http://localhost:5174` | Desktop-optimized physician OPD triage queue & workspace |
| **Clinical Database** | PostgreSQL 16 (or local Docker) | `localhost:5432/clinova` | Persistent relational store for all clinical records |

---

## 3. Pre-Demo Setup & Environment Initialization

### Step 3.1: Seed / Reset Demonstration Data
Open PowerShell and navigate to the backend directory:
```powershell
cd C:\Users\Amar\OneDrive\Desktop\Documents\clinova\Clinova-sih\backend
.\.venv\Scripts\python.exe scripts/demo_seed.py --reset --seed
```
*Expected Output:*
```text
[INFO] Purging synthetic demo data...
[INFO] Demo data reset completed successfully.
[INFO] Created Demo Hospital: Demo General Hospital
[INFO] Created Attending Physician: doctor@demohospital.org
[INFO] Seeded Consultation A: Rohan Patil (Encounter: #E47FFFEA)
[INFO] Seeded Consultation B (Red Flag): Ananya Deshmukh (Encounter: #184F0CF8)
[INFO] All demo records committed successfully!
```

---

### Step 3.2: Launch Services (Three Dedicated Terminals)

#### Terminal 1: Backend API
```powershell
cd C:\Users\Amar\OneDrive\Desktop\Documents\clinova\Clinova-sih\backend
.\.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000 --reload
```
*Verify Health:* Open browser at `http://localhost:8000/api/v1/health` -> `{"status": "healthy"}`.

#### Terminal 2: Patient Web Portal
```powershell
cd C:\Users\Amar\OneDrive\Desktop\Documents\clinova\Clinova-sih\clients\patient-web
npm run dev
```
*URL:* `http://localhost:5173`

#### Terminal 3: Hospital Web Portal
```powershell
cd C:\Users\Amar\OneDrive\Desktop\Documents\clinova\Clinova-sih\clients\hospital-web
npm run dev
```
*URL:* `http://localhost:5174`

---

## 4. Step-by-Step Demonstration Presentation Guide

### Scenario 1: Standard Clinical Flow (Patient Rohan Patil)

#### Phase A: Patient Pre-Intake Experience (`http://localhost:5173`)
1. **Landing & Identity**:
   - Open `http://localhost:5173`. Point out clean, reassuring clinical branding.
   - Click **"Existing Patient Sign-In"** and enter:
     - **Email**: `rohan.patil@example.com`
     - **Password**: `PatientPass123!`
   - Shows authenticated patient profile: *Rohan Patil, 34M, ABHA: 91-4521-8890-1234*.
2. **Informed Consent**:
   - Navigate to `/consent`. Point out that Clinova enforces explicit patient consent before AI processing or record retrieval.
   - Explain the disclaimer: *Assistive AI tool only; all medical decisions remain exclusively with licensed physicians.*
3. **Language Selection**:
   - Show `/language`. Point out English, Hindi, and Marathi options.
   - Note the **AYUSH Intake (Phase 2)** badge clearly marked as disabled to respect SIH MVP scope.
4. **Adaptive Interview & Medical Timeline**:
   - Show completed dialogue turns where the patient described dry cough and evening fever, with AI clarifying lack of dyspnea/hemoptysis.
   - Show `/timeline` displaying chronological, source-attributed events (Symptom onset 5 days ago, Cetirizine 10mg PRN, Dust/Pollen allergy).
5. **Summary Review & Declaration**:
   - On `/summary`, observe the structured AI clinical draft.
   - Check the mandatory declaration: *"I have reviewed the information and confirm that it is correct."*
   - Click **"Submit to Doctor Queue"**.
   - Point out the success modal with live consultation reference ID: **`#E47FFFEA`** (confirming no hardcoded `#24` placeholder).

---

#### Phase B: Physician Review & Queue Management (`http://localhost:5174`)
1. **Clinician Authentication**:
   - Open `http://localhost:5174`.
   - Log in as Attending Physician:
     - **Email**: `doctor@demohospital.org`
     - **Password**: `HospitalPass123!`
2. **OPD Triage Queue**:
   - Shows the live OPD Queue for *Demo General Hospital*.
   - Point out **Rohan Patil** (`#E47FFFEA`) categorized with **Routine (Green)** priority.
3. **Physician Case Workspace**:
   - Click on Rohan Patil to open the full workspace.
   - Tour the four tabs:
     - **Clinical History**: Structured chief complaint, symptoms, and dialogue history.
     - **Timeline**: Visual chronological events with source provenance (AI interview vs documented history).
     - **OCR Reports**: Prescriptions and lab reports with entity extraction.
     - **Clinical Summary**: Pre-synthesized draft ready for physician validation.
4. **Physician Summary Editing & Final Confirmation**:
   - Click **"Edit Summary"** button.
   - In the modal, modify text or append clinician instruction:
     - *"Add: Recommended warm saline gargles, maintain hydration, review after 3 days if fever persists."*
   - Click **"Save Changes"**, then click **"Confirm & Sign Summary"**.
   - Point out the immediate visual update: Status changes from `Draft` to **Confirmed**, displaying the attending doctor's timestamped signature badge.

---

### Scenario 2: Emergency Red-Flag Triage Demonstration (Patient Ananya Deshmukh)

1. **High-Priority Queue Display**:
   - In the Hospital Portal (`http://localhost:5174`), observe patient **Ananya Deshmukh** (`#184F0CF8`).
   - Notice that she is pinned at the top of the queue with an animated red pulse badge: **`EMERGENCY (RED)`**.
2. **Emergency Case Workspace**:
   - Click on Ananya Deshmukh's encounter.
   - Point out the prominent Red-Flag Alert Card:
     - *Alert:* **`CRITICAL: Acute retrosternal crushing chest pain radiating to left arm and jaw with cold diaphoresis.`**
     - *Action:* **`Immediate 12-lead ECG, telemetry, and STAT physician review mandatory.`**
3. **Key Pitch to the SIH Jury**:
   > *"In an overcrowded Indian hospital where 80 patients wait in an OPD queue, Clinova's deterministic safety engine immediately detects life-threatening cardiac symptoms, elevates the patient to the top of the doctor's screen, and displays critical triage directives before the patient even walks into the consultation room."*

---

## 5. Post-Demo Reset & Cleanup

To reset the database cleanly for another evaluation round:
```powershell
cd C:\Users\Amar\OneDrive\Desktop\Documents\clinova\Clinova-sih\backend
.\.venv\Scripts\python.exe scripts/demo_seed.py --reset --seed
```

---

## 6. Troubleshooting & Operational Tips

| Issue | Root Cause | Resolution |
| :--- | :--- | :--- |
| **CORS error in browser console** | Frontend origin not in whitelist | Ensure `BACKEND_CORS_ORIGINS` in `backend/.env` includes `http://localhost:5173,http://localhost:5174`. |
| **Port conflict on 8000 / 5173 / 5174** | Another node/python process running | In PowerShell, run `Get-Process -Id (Get-NetTCPConnection -LocalPort <port>).OwningProcess | Stop-Process -Force`. |
| **Browser retains stale JWT** | Old session cached in LocalStorage | Open DevTools -> Application -> Local Storage -> Click "Clear All", then reload. |
| **Database connection refused** | PostgreSQL service not running | In Windows Services or terminal, run `Start-Service postgresql*` or verify Docker container. |
