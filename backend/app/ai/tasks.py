"""Clinical AI task type definitions.

This module defines the set of AI tasks that Clinova may route to
different providers. Task types are used by AITaskRouter to look up
the configured provider and model for each clinical use case.

IMPORTANT:
    These are architectural task definitions only.
    The actual AI capabilities for most tasks are not yet implemented.
    This module exists solely to enable routing configuration.
"""

import enum


class AITaskType(str, enum.Enum):
    """Enumeration of clinical AI task types.

    Each task type can be mapped to a different provider/model
    through environment configuration, allowing Clinova to optimise
    cost, latency, and quality independently per task.

    HISTORY_INTERVIEW       — AI-guided clinical history taking session.
                              Conversational; benefits from instruction-following.
    STRUCTURED_EXTRACTION   — Extract structured clinical data from conversation.
                              Requires reliable JSON/structured output support.
    CLINICAL_SUMMARY        — Generate a readable clinical summary from history.
                              Benefits from long-context and reasoning capability.
    DOCUMENT_ANALYSIS       — Analyse uploaded medical documents (reports, etc.).
                              May require multimodal capability.
    TRANSLATION             — Translate clinical content across Indian languages.
                              May use a specialised translation model.
    TRIAGE                  — Preliminary severity assessment from symptoms.
                              Accuracy is critical; use the most capable model.
    """

    HISTORY_INTERVIEW = "history_interview"
    STRUCTURED_EXTRACTION = "structured_extraction"
    CLINICAL_SUMMARY = "clinical_summary"
    DOCUMENT_ANALYSIS = "document_analysis"
    TRANSLATION = "translation"
    TRIAGE = "triage"
