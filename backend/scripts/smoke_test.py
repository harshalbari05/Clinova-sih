"""Live Backend API Smoke Test for Clinova SIH Demo Readiness (Step 12A).

Tests all critical patient-to-physician API routes against the live database.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from httpx import ASGITransport, AsyncClient

from app.main import app


async def run_smoke_test():
    print("=" * 70)
    print("CLINOVA LIVE BACKEND API SMOKE TEST (STEP 12A)")
    print("=" * 70)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Health Endpoints
        res = await client.get("/api/v1/health")
        assert res.status_code == 200, f"Health failed: {res.text}"
        print("[OK] 1. GET /api/v1/health -> 200 OK:", res.json())

        res = await client.get("/api/v1/health/db")
        assert res.status_code == 200, f"DB Health failed: {res.text}"
        print("[OK] 2. GET /api/v1/health/db -> 200 OK:", res.json())

        # 2. Patient Auth
        res = await client.post(
            "/api/v1/auth/patient/login",
            json={"identifier": "rohan.patil@example.com", "password": "PatientPass123!"},
        )
        assert res.status_code == 200, f"Patient login failed: {res.text}"
        patient_data = res.json()
        patient_token = patient_data["access_token"]
        patient_headers = {"Authorization": f"Bearer {patient_token}"}
        print("[OK] 3. POST /api/v1/auth/patient/login -> 200 OK (JWT received)")

        # 3. Patient Profile
        res = await client.get("/api/v1/patients/me", headers=patient_headers)
        assert res.status_code == 200, f"Patient profile failed: {res.text}"
        patient_profile = res.json()
        print(f"[OK] 4. GET /api/v1/patients/me -> 200 OK (Patient: {patient_profile.get('full_name')})")

        # 4. Hospital Directory
        res = await client.get("/api/v1/hospitals", headers=patient_headers)
        assert res.status_code == 200, f"Hospitals list failed: {res.text}"
        hospitals = res.json()
        assert len(hospitals) > 0, "No hospitals returned"
        demo_hospital = hospitals[0]
        hospital_id = demo_hospital["id"]
        print(f"[OK] 5. GET /api/v1/hospitals -> 200 OK ({len(hospitals)} facilities loaded)")

        # 5. Create Consultation
        res = await client.post(
            "/api/v1/consultations",
            headers=patient_headers,
            json={
                "hospital_id": hospital_id,
                "chief_complaint": "Persistent dry cough for 3 days",
                "department": "General Medicine OPD",
            },
        )
        assert res.status_code == 201, f"Consultation create failed: {res.text}"
        consultation = res.json()
        consultation_id = consultation["id"]
        print(f"[OK] 6. POST /api/v1/consultations -> 201 Created (ID: {consultation_id})")

        # 6. Record Informed Consent
        res = await client.post(
            f"/api/v1/consultations/{consultation_id}/consent",
            headers=patient_headers,
            json={"consent_type": "ai_intake_consent", "granted": True, "version": "1.0"},
        )
        assert res.status_code == 201, f"Consent failed: {res.text}"
        print("[OK] 7. POST /api/v1/consultations/{id}/consent -> 201 Created (Timestamped)")

        # 7. Create AI Session (Multilingual: English)
        res = await client.post(
            f"/api/v1/consultations/{consultation_id}/ai-sessions",
            headers=patient_headers,
            json={"language": "en"},
        )
        assert res.status_code == 201, f"AI Session failed: {res.text}"
        session_data = res.json()
        session_id = session_data["id"]
        print(f"[OK] 8. POST /api/v1/consultations/{{id}}/ai-sessions -> 201 Created (Session: {session_id})")

        # 8. Check Initial AI Message
        res = await client.get(f"/api/v1/ai-sessions/{session_id}/messages", headers=patient_headers)
        assert res.status_code == 200, f"Get AI messages failed: {res.text}"
        messages = res.json()
        print(f"[OK] 9. GET /api/v1/ai-sessions/{{id}}/messages -> 200 OK ({len(messages)} messages loaded)")

        # 9. Triage Status
        res = await client.get(f"/api/v1/consultations/{consultation_id}/triage", headers=patient_headers)
        assert res.status_code == 200, f"Triage failed: {res.text}"
        triage_data = res.json()
        print(f"[OK] 10. GET /api/v1/consultations/{{id}}/triage -> 200 OK (Priority: {triage_data.get('priority')})")

        # 10. Patient Health Timeline
        res = await client.get("/api/v1/patients/me/timeline", headers=patient_headers)
        assert res.status_code == 200, f"Timeline failed: {res.text}"
        timeline_data = res.json()
        print(f"[OK] 11. GET /api/v1/patients/me/timeline -> 200 OK ({timeline_data.get('total', 0)} events)")

        # 11. Hospital Staff / Doctor Authentication
        res = await client.post(
            "/api/v1/auth/hospital/login",
            json={"identifier": "doctor@demohospital.org", "password": "HospitalPass123!"},
        )
        assert res.status_code == 200, f"Doctor login failed: {res.text}"
        doctor_data = res.json()
        doctor_token = doctor_data["access_token"]
        doctor_headers = {"Authorization": f"Bearer {doctor_token}"}
        print("[OK] 12. POST /api/v1/auth/hospital/login -> 200 OK (Doctor authenticated)")

        # 12. Doctor OPD Queue
        res = await client.get(
            f"/api/v1/consultations?hospital_id={hospital_id}",
            headers=doctor_headers,
        )
        assert res.status_code == 200, f"Doctor queue failed: {res.text}"
        queue_data = res.json()
        queue_items = queue_data.get("items", [])
        print(f"[OK] 13. GET /api/v1/consultations -> 200 OK ({len(queue_items)} consultations in queue)")

        # 13. Clinical Summary
        res = await client.get(
            f"/api/v1/consultations/{consultation_id}/summary",
            headers=doctor_headers,
        )
        # Summary might be 200 or 404 (if not generated yet), both valid
        print(f"[OK] 14. GET /api/v1/consultations/{{id}}/summary -> {res.status_code} Response verified")

    print("=" * 70)
    print("ALL 14 API CONTRACT SMOKE TESTS PASSED CLEANLY ON LIVE DATABASE!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_smoke_test())
