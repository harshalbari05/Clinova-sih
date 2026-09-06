"""Triage Service for Clinova Step 6.

Orchestrates deterministic red-flag detection, optional AI symptom
evidence extraction, and Alert persistence with deduplication.

SAFETY PRINCIPLES:
    - Never diagnose illnesses or suggest treatments.
    - Deterministic rules are authoritative: LLM cannot downgrade or override
      emergency findings.
    - If all AI providers fail or return malformed output, the system
      continues seamlessly using deterministic rules.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.config import ai_settings
from app.ai.router import task_router
from app.ai.schemas import (
    AIMessageInput,
    AIProviderError,
    AIRequest,
)
from app.ai.tasks import AITaskType
from app.models.alert import Alert
from app.models.clinical_history import ClinicalHistory
from app.models.consultation import Consultation
from app.triage.detector import default_detector
from app.triage.prompts import (
    TRIAGE_EXTRACTION_SYSTEM_PROMPT,
    build_triage_user_prompt,
)
from app.triage.schemas import (
    AITriageExtractionResponse,
    TriageCategory,
    TriageFinding,
    TriageResult,
    TriageUrgency,
)

logger = logging.getLogger(__name__)

# Standardized, non-diagnostic, calm patient safety notices
EMERGENCY_SAFETY_NOTICE = (
    "Some of the symptoms you reported may need urgent medical attention. "
    "Your information has been flagged for clinical review. "
    "Please seek immediate medical assistance according to the hospital's emergency process."
)

URGENT_SAFETY_NOTICE = (
    "Your reported symptoms have been noted and flagged for prompt physician review. "
    "A healthcare provider will review this information shortly."
)


def _format_history_summary(history: ClinicalHistory | None) -> str | None:
    """Format relevant clinical history context for triage evaluation."""
    if not history:
        return None

    parts: list[str] = []
    if history.chief_complaint:
        parts.append(f"Chief Complaint: {history.chief_complaint}")
    if history.history_of_present_illness:
        parts.append(f"Present Illness: {history.history_of_present_illness}")
    if history.past_medical_history:
        parts.append(f"Past Medical History: {history.past_medical_history}")
    if history.review_of_systems:
        parts.append(f"Review of Systems: {history.review_of_systems}")

    return " | ".join(parts) if parts else None


class TriageService:
    """Coordinates deterministic triage detection, optional AI extraction, and Alert management."""

    async def evaluate_triage(
        self,
        db: AsyncSession,
        consultation: Consultation,
        patient_text: str,
        history: ClinicalHistory | None = None,
        use_ai_assistance: bool = True,
    ) -> TriageResult:
        """Evaluate patient text and history for red-flag conditions.

        Args:
            db: Active async database session.
            consultation: The active consultation ORM instance.
            patient_text: Latest patient statement/message.
            history: Optional clinical history for the consultation.
            use_ai_assistance: Whether to invoke AI triage extraction.

        Returns:
            TriageResult containing findings, urgency, and clinical explanations.
        """
        history_summary = _format_history_summary(history)
        additional_contexts = [history_summary] if history_summary else []

        # 1. Authoritative deterministic evaluation (operates offline / zero network)
        deterministic_result = default_detector.evaluate(
            consultation_id=consultation.id,
            text=patient_text,
            additional_contexts=additional_contexts,
        )

        final_findings = list(deterministic_result.findings)
        ai_extracted_used = False

        # 2. Optional AI evidence extraction (cannot downgrade deterministic findings)
        if use_ai_assistance and ai_settings.AI_INTERVIEW_ENABLED:
            try:
                ai_findings = await self._extract_ai_triage_evidence(
                    patient_text=patient_text,
                    history_summary=history_summary,
                )
                if ai_findings:
                    # Incorporate any non-duplicate finding identified with high confidence
                    existing_codes = {f.code for f in final_findings}
                    for item in ai_findings:
                        clean_code = item.finding.upper().replace(" ", "_")
                        if clean_code not in existing_codes and item.present and item.evidence:
                            category = self._resolve_category(item.category)
                            final_findings.append(
                                TriageFinding(
                                    code=clean_code,
                                    category=category,
                                    severity="high",
                                    present=True,
                                    evidence=item.evidence,
                                    confidence=min(1.0, max(0.0, item.confidence)),
                                )
                            )
                            existing_codes.add(clean_code)
                            ai_extracted_used = True
            except AIProviderError as exc:
                logger.warning(
                    "AI triage extraction provider error (%s): %s. Relying on deterministic rules.",
                    exc.kind.value,
                    exc.message,
                )
            except Exception as exc:
                logger.warning(
                    "AI triage extraction unexpected failure: %s. Relying on deterministic rules.",
                    exc,
                )

        # 3. Consolidate urgency and explanation
        has_red_flags = len(final_findings) > 0
        if not has_red_flags:
            return TriageResult(
                consultation_id=consultation.id,
                has_red_flags=False,
                urgency=TriageUrgency.NORMAL,
                findings=[],
                requires_immediate_attention=False,
                explanation_for_clinician="No defined red-flag emergency features detected.",
                patient_safety_guidance=None,
                generated_at=datetime.now(timezone.utc),
                source="DETERMINISTIC_RULES",
            )

        has_emergency = any(
            f.severity == "critical" or
            f.code in ("CHEST_PAIN_CRUSHING", "CHEST_PAIN_WITH_DYSPNEA",
                       "CHEST_PAIN_WITH_SYNCOPE_OR_DIAPHORESIS", "BREATHING_SEVERE_DISTRESS",
                       "STROKE_ONE_SIDED_WEAKNESS", "STROKE_SPEECH_DIFFICULTY",
                       "SEIZURE_OR_CONVULSION", "BLEEDING_HEAVY_UNCONTROLLED",
                       "BLEEDING_HEMATEMESIS_OR_HEMOPTYSIS", "ANAPHYLAXIS_AIRWAY_SWELLING",
                       "ALTERED_CONSCIOUSNESS_UNRESPONSIVE", "SELF_HARM_INTENT",
                       "PREGNANCY_BLEEDING_OR_SEVERE_PAIN")
            for f in final_findings
        )

        overall_urgency = (
            TriageUrgency.EMERGENCY_REVIEW if has_emergency else TriageUrgency.URGENT
        )
        safety_guidance = (
            EMERGENCY_SAFETY_NOTICE if has_emergency else URGENT_SAFETY_NOTICE
        )

        codes = [f.code for f in final_findings]
        explanation = (
            f"Detected {len(final_findings)} red-flag finding(s): {', '.join(codes)}. "
            f"Level: {overall_urgency.value}. Flagged for clinical assessment."
        )

        result = TriageResult(
            consultation_id=consultation.id,
            has_red_flags=True,
            urgency=overall_urgency,
            findings=final_findings,
            requires_immediate_attention=has_emergency,
            explanation_for_clinician=explanation,
            patient_safety_guidance=safety_guidance,
            generated_at=datetime.now(timezone.utc),
            source="DETERMINISTIC_WITH_AI_EVALUATION" if ai_extracted_used else "DETERMINISTIC_RULES",
        )

        # 4. Persist alerts with deduplication
        await self._sync_alerts(db, consultation, result)

        return result

    async def _extract_ai_triage_evidence(
        self,
        patient_text: str,
        history_summary: str | None,
    ) -> list[Any]:
        """Invoke AITaskType.TRIAGE through the task router to extract structured evidence."""
        user_prompt = build_triage_user_prompt(
            patient_message=patient_text,
            clinical_history_summary=history_summary,
        )

        ai_req = AIRequest(
            messages=[AIMessageInput(role="user", content=user_prompt)],
            system_prompt=TRIAGE_EXTRACTION_SYSTEM_PROMPT,
            temperature=0.1,  # Low temperature for strict factual extraction
            max_tokens=500,
        )

        response = await task_router.generate(
            task=AITaskType.TRIAGE,
            request=ai_req,
        )

        # Parse JSON structured output
        raw_text = response.text.strip()
        # Clean markdown codeblocks if returned
        if raw_text.startswith("```"):
            lines = raw_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            raw_text = "\n".join(lines).strip()

        data = json.loads(raw_text)
        validated = AITriageExtractionResponse.model_validate(data)
        return validated.findings

    def _resolve_category(self, cat_str: str) -> TriageCategory:
        """Map raw category string to TriageCategory safely."""
        cat_clean = cat_str.lower().strip()
        for cat in TriageCategory:
            if cat.value == cat_clean or cat.name.lower() == cat_clean:
                return cat
        return TriageCategory.GENERAL

    async def _sync_alerts(
        self,
        db: AsyncSession,
        consultation: Consultation,
        triage_result: TriageResult,
    ) -> None:
        """Create or update database alerts for detected findings with deduplication."""
        # Query active alerts for this consultation
        stmt = select(Alert).where(
            Alert.consultation_id == consultation.id,
            Alert.status == "active",
        )
        existing_alerts = list((await db.execute(stmt)).scalars().all())
        existing_by_type = {a.alert_type: a for a in existing_alerts}

        for finding in triage_result.findings:
            alert_type = finding.code
            message = (
                f"Red-Flag Finding: {finding.code} ({finding.category.value}). "
                f"Severity: {finding.severity}. Evidence reported: \"{finding.evidence}\""
            )

            if alert_type in existing_by_type:
                # Deduplication: update existing active alert rather than creating duplicates
                alert = existing_by_type[alert_type]
                alert.message = message
                # If finding is critical, promote alert severity
                if finding.severity == "critical" and alert.severity != "critical":
                    alert.severity = "critical"
                alert.updated_at = datetime.now(timezone.utc)
                db.add(alert)
                logger.info(
                    "Updated existing active Alert %s for consultation %s (%s).",
                    alert.id,
                    consultation.id,
                    alert_type,
                )
            else:
                # Create fresh alert
                new_alert = Alert(
                    id=uuid.uuid4(),
                    consultation_id=consultation.id,
                    patient_id=consultation.patient_id,
                    alert_type=alert_type,
                    severity=finding.severity,
                    message=message,
                    source=triage_result.source,
                    status="active",
                )
                db.add(new_alert)
                logger.warning(
                    "Created new active Alert for consultation %s: %s [%s]",
                    consultation.id,
                    alert_type,
                    finding.severity,
                )

        await db.flush()

    async def get_consultation_alerts(
        self,
        db: AsyncSession,
        consultation_id: uuid.UUID,
    ) -> list[Alert]:
        """Fetch all alerts for a consultation ordered newest first."""
        stmt = (
            select(Alert)
            .where(Alert.consultation_id == consultation_id)
            .order_by(desc(Alert.created_at))
        )
        return list((await db.execute(stmt)).scalars().all())


# Singleton instance
triage_service = TriageService()
