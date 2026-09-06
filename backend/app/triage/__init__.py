"""Clinova Triage and Red-Flag Detection Package."""

from app.triage.detector import DeterministicTriageDetector, default_detector
from app.triage.rules import RED_FLAG_RULES, RedFlagRule
from app.triage.schemas import (
    TriageCategory,
    TriageFinding,
    TriageResult,
    TriageUrgency,
)
from app.triage.service import (
    EMERGENCY_SAFETY_NOTICE,
    URGENT_SAFETY_NOTICE,
    TriageService,
    triage_service,
)

__all__ = [
    "DeterministicTriageDetector",
    "EMERGENCY_SAFETY_NOTICE",
    "RED_FLAG_RULES",
    "RedFlagRule",
    "TriageCategory",
    "TriageFinding",
    "TriageResult",
    "TriageService",
    "TriageUrgency",
    "URGENT_SAFETY_NOTICE",
    "default_detector",
    "triage_service",
]
