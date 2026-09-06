"""AI-powered structured extraction service for medical documents.

Invokes the multi-provider AITaskRouter with task AITaskType.STRUCTURED_EXTRACTION.
Validates output against strict Pydantic schemas and ensures non-diagnostic safety.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import ValidationError

from app.ai.prompts.document_extraction import (
    DOCUMENT_EXTRACTION_SYSTEM_PROMPT,
    build_document_extraction_user_prompt,
)
from app.ai.router import task_router
from app.ai.schemas import AIMessageInput, AIProviderError, AIRequest
from app.ai.tasks import AITaskType
from app.documents.ocr.base import OCRResult
from app.documents.schemas import DocumentExtraction

logger = logging.getLogger(__name__)


class DocumentExtractionService:
    """Extracts structured medical information using AITaskRouter."""

    async def extract_structured_data(
        self,
        ocr_result: OCRResult,
        claimed_type: str | None = None,
        document_date_hint: str | None = None,
    ) -> tuple[DocumentExtraction | None, list[str]]:
        """Run structured extraction through the configured AI fallback chain.

        Returns (DocumentExtraction, warnings). If AI extraction fails, returns
        (None, warnings) allowing the system to preserve OCR text and document safely.
        """
        raw_text = ocr_result.text.strip()
        warnings = list(ocr_result.warnings)

        if not raw_text:
            warnings.append("Skipped AI extraction: document contains no readable text.")
            return None, warnings

        # Build prompt with page markers
        user_prompt = build_document_extraction_user_prompt(
            document_text=raw_text,
            claimed_type=claimed_type,
            document_date_hint=document_date_hint,
        )

        ai_req = AIRequest(
            messages=[AIMessageInput(role="user", content=user_prompt)],
            system_prompt=DOCUMENT_EXTRACTION_SYSTEM_PROMPT,
            temperature=0.1,  # Low temperature for deterministic factual extraction
            max_tokens=2500,
        )

        try:
            response = await task_router.generate(
                task=AITaskType.STRUCTURED_EXTRACTION,
                request=ai_req,
            )
        except AIProviderError as exc:
            logger.warning(
                "AI structured extraction failed with provider error (%s): %s",
                exc.kind.value,
                exc.message,
            )
            warnings.append(f"AI extraction provider error: {exc.message}")
            return None, warnings
        except Exception as exc:
            logger.warning("AI structured extraction unexpected failure: %s", exc)
            warnings.append(f"AI extraction failed: {exc}")
            return None, warnings

        # Strip markdown fences if present
        text_out = response.text.strip()
        if text_out.startswith("```"):
            lines = text_out.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text_out = "\n".join(lines).strip()

        # Parse and validate JSON
        try:
            parsed = json.loads(text_out)
        except json.JSONDecodeError as exc:
            logger.warning("AI structured extraction returned malformed JSON: %s", exc)
            warnings.append("AI model returned malformed output that could not be parsed as JSON.")
            return None, warnings

        try:
            extraction = DocumentExtraction.model_validate(parsed)
            # Merge any provider warnings
            if extraction.warnings:
                warnings.extend(extraction.warnings)
            return extraction, warnings
        except ValidationError as val_err:
            logger.warning("AI structured extraction schema validation failed: %s", val_err)
            warnings.append("Extracted output did not strictly conform to the clinical schema.")
            return None, warnings


# Singleton instance
document_extraction_service = DocumentExtractionService()
