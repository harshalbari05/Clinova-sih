"""AI and Deterministic Clinical Summary Generator for Step 9.

Implements safe, non-diagnostic pre-consultation clinical summary generation.
Uses AITaskRouter with task AITaskType.CLINICAL_SUMMARY and provides a guaranteed
deterministic fallback if AI providers are offline, unavailable, or return malformed JSON.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import ValidationError

from app.ai.prompts.clinical_summary import (
    CLINICAL_SUMMARY_SYSTEM_PROMPT,
    build_clinical_summary_user_prompt,
)
from app.ai.router import task_router
from app.ai.schemas import AIMessageInput, AIProviderError, AIRequest
from app.ai.tasks import AITaskType
from app.schemas.summary import (
    ProvenanceItem,
    StructuredSummary,
    SummaryAllergy,
    SummaryInvestigation,
    SummaryMedication,
    SummarySourceType,
    SummaryTimelineEvent,
    SummaryTriageAlert,
)

logger = logging.getLogger(__name__)


class ClinicalSummaryGenerator:
    """Generates structured pre-consultation clinical summaries."""

    async def generate_summary(
        self, context: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        """Generate a clinical summary draft using AI with deterministic fallback.

        Returns (summary_text, structured_summary_dict).
        """
        user_prompt = build_clinical_summary_user_prompt(context)
        ai_req = AIRequest(
            messages=[AIMessageInput(role="user", content=user_prompt)],
            system_prompt=CLINICAL_SUMMARY_SYSTEM_PROMPT,
            temperature=0.1,  # Low temperature for objective factual synthesis
            max_tokens=3000,
        )

        try:
            ai_response = await task_router.generate(
                task=AITaskType.CLINICAL_SUMMARY,
                request=ai_req,
            )
            text_out = ai_response.text.strip()

            # Strip markdown code fences if present
            if text_out.startswith("```"):
                lines = text_out.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                text_out = "\n".join(lines).strip()

            parsed = json.loads(text_out)
            structured = StructuredSummary.model_validate(parsed)
            summary_text = self._build_prose_summary(structured, context)
            return summary_text, structured.model_dump()

        except (AIProviderError, json.JSONDecodeError, ValidationError, Exception) as exc:
            logger.info(
                "AI summary generation failed or unavailable (%s). Using deterministic fallback.",
                exc,
            )
            structured = self._build_deterministic_summary(context)
            summary_text = self._build_prose_summary(structured, context)
            return summary_text, structured.model_dump()

    def _build_deterministic_summary(self, context: dict[str, Any]) -> StructuredSummary:
        """Deterministically synthesizes a grounded StructuredSummary from context."""
        consultation = context.get("consultation", {})
        history = context.get("clinical_history", {})
        interview = context.get("interview", {})
        alerts = context.get("alerts", [])
        documents = context.get("documents", [])
        timeline = context.get("timeline_highlights", [])

        chief_complaint = (
            consultation.get("chief_complaint")
            or history.get("chief_complaint")
            or "Patient presenting for clinical evaluation"
        )
        hpi = history.get("history_of_present_illness") or "No formal HPI documented."

        # Patient reported symptoms from interview
        symptoms: list[ProvenanceItem] = []
        for sym in interview.get("symptoms", []):
            if isinstance(sym, dict):
                raw_name = sym.get("name") or sym.get("symptom")
                name = str(raw_name).strip() if raw_name else ""
                ev = sym.get("evidence")
                ev_str = str(ev) if ev is not None else None
            else:
                name = str(sym).strip()
                ev_str = None

            if not name:
                continue

            symptoms.append(
                ProvenanceItem(
                    item=name,
                    source_type=SummarySourceType.PATIENT_REPORTED.value,
                    evidence=ev_str,
                )
            )
        # If interview turns had patient messages, capture them
        for turn in interview.get("turns", []):
            pt_msg = turn.get("patient_message")
            if pt_msg and not any(str(pt_msg) in s.item for s in symptoms):
                symptoms.append(
                    ProvenanceItem(
                        item=str(pt_msg),
                        source_type=SummarySourceType.PATIENT_REPORTED.value,
                        evidence=str(pt_msg),
                    )
                )

        # Past Medical History
        pmh_items: list[ProvenanceItem] = []
        if history.get("past_medical_history"):
            pmh_items.append(
                ProvenanceItem(
                    item=str(history["past_medical_history"]),
                    source_type=SummarySourceType.CLINICAL_HISTORY.value,
                )
            )

        # Past Surgical History
        psh_items: list[ProvenanceItem] = []
        if history.get("past_surgical_history"):
            psh_items.append(
                ProvenanceItem(
                    item=str(history["past_surgical_history"]),
                    source_type=SummarySourceType.CLINICAL_HISTORY.value,
                )
            )

        # Medications
        medications: list[SummaryMedication] = []
        # From clinical history
        if history.get("drug_history"):
            medications.append(
                SummaryMedication(
                    name=str(history["drug_history"]),
                    source_type=SummarySourceType.CLINICAL_HISTORY.value,
                )
            )
        # From documents
        for doc in documents:
            ext = doc.get("extractions") or {}
            for med in ext.get("medications", []):
                medications.append(
                    SummaryMedication(
                        name=str(med.get("name_as_written") or "Unknown medication"),
                        dosage=med.get("dose_as_written"),
                        frequency=med.get("frequency_as_written"),
                        source_type=SummarySourceType.DOCUMENT_EXTRACTED.value,
                        evidence=med.get("evidence"),
                    )
                )
            for diag in ext.get("diagnoses_or_conditions_as_documented", []):
                if diag:
                    pmh_items.append(
                        ProvenanceItem(
                            item=str(diag),
                            source_type=SummarySourceType.DOCUMENT_EXTRACTED.value,
                            evidence=f"Document: {doc.get('file_name')}",
                        )
                    )

        # Allergies
        allergies: list[SummaryAllergy] = []
        if history.get("allergy_history"):
            allergies.append(
                SummaryAllergy(
                    allergen=str(history["allergy_history"]),
                    source_type=SummarySourceType.CLINICAL_HISTORY.value,
                )
            )

        # Family & Social
        family_social: list[ProvenanceItem] = []
        if history.get("family_history"):
            family_social.append(
                ProvenanceItem(
                    item=f"Family History: {history['family_history']}",
                    source_type=SummarySourceType.CLINICAL_HISTORY.value,
                )
            )
        if history.get("personal_history"):
            family_social.append(
                ProvenanceItem(
                    item=f"Personal/Social History: {history['personal_history']}",
                    source_type=SummarySourceType.CLINICAL_HISTORY.value,
                )
            )

        # Investigations
        investigations: list[SummaryInvestigation] = []
        for doc in documents:
            ext = doc.get("extractions") or {}
            for lab in ext.get("laboratory_results", []):
                investigations.append(
                    SummaryInvestigation(
                        test_name=lab.get("test_name", "Laboratory Test"),
                        result_value=str(lab.get("result_value", "")),
                        unit=lab.get("unit"),
                        reference_range=lab.get("reference_range"),
                        flag=lab.get("abnormal_flag"),
                        source_document=doc.get("file_name"),
                        evidence=lab.get("evidence"),
                    )
                )

        # Triage & Red flags
        triage_alerts: list[SummaryTriageAlert] = []
        for alert in alerts:
            triage_alerts.append(
                SummaryTriageAlert(
                    alert_type=alert.get("alert_type", "Alert"),
                    severity=alert.get("severity", "medium"),
                    message=alert.get("message", ""),
                    status=alert.get("status", "active"),
                )
            )

        # Timeline
        timeline_highlights: list[SummaryTimelineEvent] = []
        for ev in timeline:
            timeline_highlights.append(
                SummaryTimelineEvent(
                    event_date=ev.get("event_date"),
                    event_type=ev.get("event_type", "EVENT"),
                    title=ev.get("title", ""),
                    verification_status=ev.get("verification_status", "UNVERIFIED"),
                )
            )

        # Missing areas
        unclear_areas: list[str] = []
        if not history.get("allergy_history"):
            unclear_areas.append("Allergy history not formally documented.")
        if not history.get("past_medical_history") and not pmh_items:
            unclear_areas.append("Past medical history is empty.")
        if not history.get("drug_history") and not medications:
            unclear_areas.append("No active medications recorded.")

        return StructuredSummary(
            chief_complaint=chief_complaint,
            history_of_present_illness=hpi,
            patient_reported_symptoms=symptoms,
            past_medical_history=pmh_items,
            past_surgical_history=psh_items,
            current_medications=medications,
            allergies=allergies,
            family_and_social_history=family_social,
            relevant_investigations=investigations,
            triage_and_red_flags=triage_alerts,
            timeline_highlights=timeline_highlights,
            unreported_or_unclear_areas=unclear_areas,
            disclaimer=(
                "AI-generated clinical draft for physician review only. "
                "Not a medical diagnosis or treatment plan."
            ),
        )

    def _build_prose_summary(
        self, structured: StructuredSummary, context: dict[str, Any]
    ) -> str:
        """Generates clear, physician-ready prose from structured summary facts."""
        patient = context.get("patient", {})
        patient_name = patient.get("name", "Patient")
        gender = patient.get("gender", "")
        age = patient.get("dob")

        lines: list[str] = []
        demographics = []
        if age:
            demographics.append(f"DOB: {age}")
        if gender:
            demographics.append(gender)
        demo_str = f" ({', '.join(demographics)})" if demographics else ""

        lines.append(f"CLINICAL SUMMARY DRAFT FOR PHYSICIAN REVIEW")
        lines.append(f"Patient: {patient_name}{demo_str}")
        lines.append(f"Chief Complaint: {structured.chief_complaint or 'None documented'}")
        lines.append("")

        # Red flags banner if any
        if structured.triage_and_red_flags:
            lines.append("⚠️ RED FLAG ALERTS / TRIAGE FINDINGS:")
            for alert in structured.triage_and_red_flags:
                lines.append(f"- [{alert.severity.upper()}] {alert.alert_type}: {alert.message}")
            lines.append("")

        # HPI
        if structured.history_of_present_illness:
            lines.append("History of Present Illness:")
            lines.append(structured.history_of_present_illness)
            lines.append("")

        # Patient reported symptoms
        if structured.patient_reported_symptoms:
            lines.append("Patient-Reported Symptoms & Statements:")
            for sym in structured.patient_reported_symptoms:
                ev_str = f' (evidence: "{sym.evidence}")' if sym.evidence else ""
                lines.append(f"- {sym.item}{ev_str}")
            lines.append("")

        # Past Medical & Surgical History
        if structured.past_medical_history:
            lines.append("Past Medical History:")
            for item in structured.past_medical_history:
                lines.append(f"- [{item.source_type}] {item.item}")
            lines.append("")

        if structured.past_surgical_history:
            lines.append("Past Surgical History:")
            for item in structured.past_surgical_history:
                lines.append(f"- [{item.source_type}] {item.item}")
            lines.append("")

        # Medications
        if structured.current_medications:
            lines.append("Current Medications:")
            for med in structured.current_medications:
                details = []
                if med.dosage:
                    details.append(med.dosage)
                if med.frequency:
                    details.append(med.frequency)
                det_str = f" ({', '.join(details)})" if details else ""
                lines.append(f"- [{med.source_type}] {med.name}{det_str}")
            lines.append("")

        # Allergies
        if structured.allergies:
            lines.append("Documented Allergies:")
            for alg in structured.allergies:
                react = f" - Reaction: {alg.reaction}" if alg.reaction else ""
                lines.append(f"- {alg.allergen}{react}")
            lines.append("")

        # Investigations
        if structured.relevant_investigations:
            lines.append("Laboratory & Investigation Highlights:")
            for inv in structured.relevant_investigations:
                flag_str = f" [{inv.flag}]" if inv.flag else ""
                unit_str = f" {inv.unit}" if inv.unit else ""
                ref_str = f" (Ref: {inv.reference_range})" if inv.reference_range else ""
                lines.append(f"- {inv.test_name}: {inv.result_value}{unit_str}{flag_str}{ref_str}")
            lines.append("")

        # Unclear areas
        if structured.unreported_or_unclear_areas:
            lines.append("Information Gaps / Unreported Areas:")
            for gap in structured.unreported_or_unclear_areas:
                lines.append(f"- {gap}")
            lines.append("")

        # Disclaimer
        lines.append(f"Note: {structured.disclaimer}")

        return "\n".join(lines)


clinical_summary_generator = ClinicalSummaryGenerator()
