"""LLM response parser and validator for the clinical interview engine.

This module is the ONLY place where raw LLM output is converted to
structured clinical data. It enforces Pydantic validation before
any data reaches the clinical history layer.

Safety contract:
    - NEVER write unvalidated LLM text directly to ClinicalHistory.
    - NEVER accept fields not defined in ClinicalInterviewAIResponse.
    - NEVER accept empty next_question.
    - If parsing fails → raise ValueError → caller uses safe fallback.
    - Diagnosis/prescription fields cannot appear in the schema (by design).

Parsing strategy:
    1. If AIResponse.structured is already a dict → try to validate directly.
    2. Else → try to extract JSON from AIResponse.text.
    3. If both fail → raise ValueError with clear reason.
"""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError

from app.ai.interview.schemas import ClinicalInterviewAIResponse

if TYPE_CHECKING:
    from app.ai.schemas import AIResponse

logger = logging.getLogger(__name__)

__all__ = ["parse_interview_response"]

# Regex to extract a JSON block from text output (handles ```json ... ``` fences)
_JSON_BLOCK_RE = re.compile(
    r"```(?:json)?\s*(\{.*?\})\s*```",
    re.DOTALL,
)
# Fallback: find first {...} in plain text
_JSON_INLINE_RE = re.compile(r"\{.*\}", re.DOTALL)


def parse_interview_response(
    ai_response: "AIResponse",
) -> ClinicalInterviewAIResponse:
    """Parse and validate the LLM's structured interview response.

    Attempts multiple strategies in order:
    1. Use the pre-parsed `structured` dict if available (provider already
       parsed JSON — e.g., Ollama in json mode, OpenAI with json_schema).
    2. Extract a JSON block from the raw text (handles ```json fences).
    3. Extract the first {...} object from plain text.

    Args:
        ai_response: The AIResponse returned by the provider adapter.

    Returns:
        Validated ClinicalInterviewAIResponse.

    Raises:
        ValueError: If no valid structured response can be parsed or validated.
                    The caller should NOT write anything to ClinicalHistory
                    when this is raised.
    """
    # Strategy 1: provider returned pre-parsed structured dict
    if ai_response.structured and isinstance(ai_response.structured, dict):
        return _validate_dict(ai_response.structured, strategy="structured_field")

    # Strategy 2: try to parse from raw text
    raw_text = (ai_response.text or "").strip()
    if not raw_text:
        raise ValueError("LLM returned empty response — cannot parse interview data.")

    # Try code-fence JSON first
    match = _JSON_BLOCK_RE.search(raw_text)
    if match:
        return _parse_json_and_validate(match.group(1), strategy="json_fence")

    # Try bare JSON object in text
    match = _JSON_INLINE_RE.search(raw_text)
    if match:
        return _parse_json_and_validate(match.group(0), strategy="json_inline")

    # No JSON found — the response might be plain conversational text.
    # This happens with models that don't follow structured output instructions.
    # Treat the raw text as the next_question with no extraction.
    logger.warning(
        "LLM response from '%s' does not contain JSON. "
        "Wrapping plain text as next_question (no extraction).",
        ai_response.provider,
    )
    # Build a minimal valid response with just the question
    return ClinicalInterviewAIResponse(next_question=raw_text[:1000])


def _parse_json_and_validate(json_str: str, strategy: str) -> ClinicalInterviewAIResponse:
    """Parse a JSON string and validate it as ClinicalInterviewAIResponse."""
    try:
        data: Any = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"LLM returned invalid JSON ({strategy}): {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(
            f"LLM JSON is not a dict ({strategy}): got {type(data).__name__}"
        )

    return _validate_dict(data, strategy=strategy)


def _validate_dict(
    data: dict[str, Any],
    strategy: str,
) -> ClinicalInterviewAIResponse:
    """Run Pydantic validation on a parsed dict."""
    try:
        result = ClinicalInterviewAIResponse.model_validate(data)
        logger.debug(
            "Interview response parsed via strategy='%s'. "
            "section=%s, complete=%s, extracted=%s.",
            strategy,
            result.current_section,
            result.interview_complete,
            result.extracted_information is not None,
        )
        return result
    except ValidationError as exc:
        raise ValueError(
            f"LLM response failed Pydantic validation ({strategy}): {exc}"
        ) from exc
