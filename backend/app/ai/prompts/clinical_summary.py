"""Prompts for AI Clinical Summary generation (Step 9).

CLINICAL SAFETY MANDATES:
- NON-DIAGNOSTIC: Never diagnose illnesses, declare prognoses, or synthesize clinical opinions.
- NON-PRESCRIPTIVE: Never prescribe medications, suggest dosages, or advise treatment courses.
- GROUNDED: Extract and synthesize ONLY what is explicitly documented or stated.
- ATTRIBUTION: Explicitly categorize findings under PATIENT_REPORTED, DOCUMENT_EXTRACTED,
  CLINICAL_HISTORY, or TRIAGE_ALERT.
- STRICT JSON: Return valid JSON matching the StructuredSummary schema.
"""

from __future__ import annotations

import json
from typing import Any

CLINICAL_SUMMARY_SYSTEM_PROMPT = """You are Clinova's Pre-Consultation Clinical Summary Engine.
Your role is to synthesize pre-consultation information gathered from patient interviews, uploaded documents, clinical history, and triage alerts into an objective, evidence-backed draft summary for the reviewing physician.

CRITICAL CLINICAL SAFETY RULES:
1. NON-DIAGNOSTIC ROLE:
   - You are an assistive documentation tool, NOT a physician.
   - You must NOT diagnose illnesses, declare prognoses, or suggest differential diagnoses.
   - Only document conditions or diagnoses that are EXPLICITLY documented by clinicians in uploaded records or reported as prior diagnoses by the patient.

2. NO MEDICAL PRESCRIPTIONS OR ADVICE:
   - Never recommend medications, dose adjustments, therapies, or clinical interventions.
   - Only summarize medications and treatments explicitly reported as currently taken or previously prescribed in records.

3. STRICT GROUNDING & NO HALLUCINATION:
   - Only summarize information present in the provided clinical data.
   - Never infer unmentioned facts. If data for a clinical category is missing or ambiguous, document it under "unreported_or_unclear_areas".

4. SOURCE ATTRIBUTION & PROVENANCE:
   - Every symptom, medication, condition, and finding must be attributed to its source type:
     * "PATIENT_REPORTED": Reported verbally or via chat by the patient.
     * "DOCUMENT_EXTRACTED": Extracted from uploaded medical records/prescriptions/labs.
     * "CLINICAL_HISTORY": From structured prior clinical history records.
     * "TRIAGE_ALERT": From automated red-flag triage detection.
   - Where available, preserve verbatim quotes as "evidence".

5. JSON SCHEMA:
   Return valid JSON with the exact structure below:
{
  "chief_complaint": string or null,
  "history_of_present_illness": string or null,
  "patient_reported_symptoms": [
    {
      "item": string,
      "source_type": "PATIENT_REPORTED",
      "source_id": string or null,
      "evidence": string or null
    }
  ],
  "past_medical_history": [
    {
      "item": string,
      "source_type": string,
      "source_id": string or null,
      "evidence": string or null
    }
  ],
  "past_surgical_history": [
    {
      "item": string,
      "source_type": string,
      "source_id": string or null,
      "evidence": string or null
    }
  ],
  "current_medications": [
    {
      "name": string,
      "dosage": string or null,
      "frequency": string or null,
      "source_type": string,
      "evidence": string or null
    }
  ],
  "allergies": [
    {
      "allergen": string,
      "reaction": string or null,
      "severity": string or null,
      "source_type": string
    }
  ],
  "family_and_social_history": [
    {
      "item": string,
      "source_type": string,
      "source_id": string or null,
      "evidence": string or null
    }
  ],
  "relevant_investigations": [
    {
      "test_name": string,
      "result_value": string,
      "unit": string or null,
      "reference_range": string or null,
      "flag": string or null,
      "source_document": string or null,
      "evidence": string or null
    }
  ],
  "triage_and_red_flags": [
    {
      "alert_type": string,
      "severity": string,
      "message": string,
      "status": string
    }
  ],
  "timeline_highlights": [
    {
      "event_date": string or null,
      "event_type": string,
      "title": string,
      "verification_status": string
    }
  ],
  "unreported_or_unclear_areas": [string],
  "disclaimer": "AI-generated clinical draft for physician review only. Not a medical diagnosis or treatment plan."
}
"""


def build_clinical_summary_user_prompt(context: dict[str, Any]) -> str:
    """Formats assembled clinical context into structured markdown for the prompt."""
    sections: list[str] = [
        "Please generate an objective, non-diagnostic pre-consultation clinical draft summary based on the following patient records:\n"
    ]

    # 1. Patient Profile
    patient = context.get("patient", {})
    sections.append("### Patient Demographics:")
    sections.append(f"- Name: {patient.get('name', 'Not specified')}")
    sections.append(f"- Gender: {patient.get('gender', 'Unknown')}")
    sections.append(f"- Age/DOB: {patient.get('dob', 'Unknown')}")
    sections.append(f"- Blood Group: {patient.get('blood_group', 'Unknown')}\n")

    # 2. Consultation Details
    consultation = context.get("consultation", {})
    sections.append("### Current Consultation:")
    sections.append(f"- Chief Complaint: {consultation.get('chief_complaint', 'None stated')}")
    sections.append(f"- Status: {consultation.get('status', 'initiated')}\n")

    # 3. Triage Alerts / Red Flags
    alerts = context.get("alerts", [])
    sections.append(f"### Triage Alerts & Red Flags ({len(alerts)} items):")
    if alerts:
        for alert in alerts:
            sections.append(
                f"- [{alert.get('severity', 'UNKNOWN').upper()}] {alert.get('alert_type')}: {alert.get('message')}"
            )
    else:
        sections.append("- No active red flag alerts detected.")
    sections.append("")

    # 4. AI Clinical Interview Findings
    interview = context.get("interview", {})
    sections.append("### AI Clinical Interview Findings:")
    symptoms = interview.get("symptoms", [])
    if symptoms:
        for s in symptoms:
            name = s.get("name") if isinstance(s, dict) else s
            sections.append(f"- Symptom reported: {name}")
    turns = interview.get("turns", [])
    if turns:
        sections.append(f"- Total interview turns completed: {len(turns)}")
        sections.append("Key patient statements:")
        for turn in turns[-5:]:  # Recent turns
            sections.append(f"  * Patient: \"{turn.get('patient_message', '')}\"")
    if not symptoms and not turns:
        sections.append("- No AI interview conversation conducted.")
    sections.append("")

    # 5. Structured Clinical History
    history = context.get("clinical_history", {})
    sections.append("### Prior Clinical History:")
    if history:
        for k, v in history.items():
            if v:
                label = k.replace("_", " ").title()
                sections.append(f"- {label}: {v}")
    else:
        sections.append("- No prior clinical history recorded.")
    sections.append("")

    # 6. Medical Documents & Extracted Findings
    documents = context.get("documents", [])
    sections.append(f"### Medical Documents & Records ({len(documents)} documents):")
    if documents:
        for doc in documents:
            sections.append(f"Document: {doc.get('document_type', 'Document')} ({doc.get('file_name', 'Unnamed')})")
            extractions = doc.get("extractions", {})
            if extractions:
                doc_meds = extractions.get("medications", [])
                if doc_meds:
                    sections.append(f"  * Documented Medications: {json.dumps(doc_meds)}")
                doc_labs = extractions.get("laboratory_results", [])
                if doc_labs:
                    sections.append(f"  * Documented Labs: {json.dumps(doc_labs)}")
                doc_diag = extractions.get("diagnoses_or_conditions_as_documented", [])
                if doc_diag:
                    sections.append(f"  * Documented Impressions/Diagnoses: {', '.join(doc_diag)}")
    else:
        sections.append("- No medical documents uploaded.")
    sections.append("")

    # 7. Timeline Highlights
    timeline = context.get("timeline_highlights", [])
    sections.append(f"### Chronological Medical Timeline ({len(timeline)} events):")
    if timeline:
        for ev in timeline[:8]:
            date_str = ev.get("event_date", "Date unknown")
            sections.append(f"- [{date_str}] ({ev.get('event_type')}) {ev.get('title')} [{ev.get('verification_status')}]")
    else:
        sections.append("- No timeline milestones recorded.")
    sections.append("")

    sections.append("Synthesize this data strictly into the requested JSON schema.")
    return "\n".join(sections)
