"""Deterministic Red-Flag Detector for Clinova.

Evaluates clinical narratives, patient messages, and structured history
against the deterministic red-flag rule set.

AUTHORITATIVE DESIGN:
    - This detector is completely deterministic and operates offline.
    - Findings produced by this engine take precedence over any LLM suggestion.
    - LLM cannot downgrade or suppress findings discovered here.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from app.triage.rules import RED_FLAG_RULES, RedFlagRule
from app.triage.schemas import (
    TriageFinding,
    TriageResult,
    TriageUrgency,
)


class DeterministicTriageDetector:
    """Evaluates clinical texts against authoritative deterministic red-flag rules."""

    def __init__(self, rules: list[RedFlagRule] | None = None) -> None:
        self.rules = rules if rules is not None else RED_FLAG_RULES

    def evaluate(
        self,
        consultation_id: uuid.UUID,
        text: str,
        additional_contexts: list[str] | None = None,
    ) -> TriageResult:
        """Analyze text and optional context segments for red flags.

        Args:
            consultation_id: UUID of the consultation being evaluated.
            text: Primary patient text (e.g. latest patient message).
            additional_contexts: Optional list of additional strings
                                (e.g. chief_complaint, history_of_present_illness).

        Returns:
            TriageResult containing findings, urgency, and explanation.
        """
        # Combine texts cleanly
        all_segments = [text]
        if additional_contexts:
            for ctx in additional_contexts:
                if ctx and ctx.strip():
                    all_segments.append(ctx.strip())

        full_text = " ".join(all_segments)
        norm_text = self._normalize_text(full_text)

        findings: list[TriageFinding] = []

        for rule in self.rules:
            matched, evidence = self._evaluate_rule(rule, norm_text)
            if matched and evidence:
                findings.append(
                    TriageFinding(
                        code=rule.code,
                        category=rule.category,
                        severity=rule.severity,
                        present=True,
                        evidence=evidence,
                        confidence=1.0,
                    )
                )

        if not findings:
            return TriageResult(
                consultation_id=consultation_id,
                has_red_flags=False,
                urgency=TriageUrgency.NORMAL,
                findings=[],
                requires_immediate_attention=False,
                explanation_for_clinician=(
                    "No defined red-flag emergency features detected from reported symptoms."
                ),
                patient_safety_guidance=None,
                generated_at=datetime.now(timezone.utc),
                source="DETERMINISTIC_RULES",
            )

        # Determine highest urgency among matched findings
        has_emergency = any(
            f.severity == "critical" or
            any(r.code == f.code and r.urgency == TriageUrgency.EMERGENCY_REVIEW for r in self.rules)
            for f in findings
        )

        overall_urgency = (
            TriageUrgency.EMERGENCY_REVIEW if has_emergency else TriageUrgency.URGENT
        )

        codes = [f.code for f in findings]
        explanation = (
            f"Detected {len(findings)} red-flag finding(s): {', '.join(codes)}. "
            "Flagged for prompt physician assessment."
        )

        return TriageResult(
            consultation_id=consultation_id,
            has_red_flags=True,
            urgency=overall_urgency,
            findings=findings,
            requires_immediate_attention=(overall_urgency == TriageUrgency.EMERGENCY_REVIEW),
            explanation_for_clinician=explanation,
            patient_safety_guidance=None,
            generated_at=datetime.now(timezone.utc),
            source="DETERMINISTIC_RULES",
        )

    def _normalize_text(self, text: str) -> str:
        """Clean and normalize whitespace and casing."""
        lower = text.lower()
        # Replace punctuation with spaces except hyphens/apostrophes
        cleaned = re.sub(r"[^\w\s\'-]", " ", lower)
        return " ".join(cleaned.split())

    def _evaluate_rule(
        self,
        rule: RedFlagRule,
        normalized_text: str,
    ) -> tuple[bool, str | None]:
        """Check whether a single rule triggers on the normalized text."""
        # 1. Check if an explicit negation pattern matches
        for neg_pat in rule.negation_patterns:
            if re.search(neg_pat, normalized_text, re.IGNORECASE):
                return False, None

        # 2. Check if primary pattern matches
        primary_match: re.Match[str] | None = None
        for pat in rule.patterns:
            m = re.search(pat, normalized_text, re.IGNORECASE)
            if m:
                primary_match = m
                break

        if not primary_match:
            return False, None

        primary_evidence = primary_match.group(0)

        # 3. Check conjunction pattern (if required)
        if rule.required_conjunction_patterns:
            conj_match: re.Match[str] | None = None
            for conj_pat in rule.required_conjunction_patterns:
                m = re.search(conj_pat, normalized_text, re.IGNORECASE)
                if m:
                    conj_match = m
                    break

            if not conj_match:
                return False, None

            conj_evidence = conj_match.group(0)
            combined_evidence = f"{primary_evidence} + {conj_evidence}"
            return True, combined_evidence

        return True, primary_evidence


# Module-level default detector
default_detector = DeterministicTriageDetector()
