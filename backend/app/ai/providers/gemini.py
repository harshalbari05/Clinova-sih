"""Google Gemini provider adapter for Clinova.

SDK dependency: google-genai >= 1.0.0
    Install: pip install google-genai

ISOLATION RULE:
    google.genai imports are CONFINED to this module.
    No other Clinova module may import google.genai directly.

Lazy initialisation:
    The SDK client is created on the first call to generate().
    Application startup does NOT require GEMINI_API_KEY to be set
    unless Gemini is the selected provider for an active task.

Structured output:
    When request.response_format is provided, the adapter passes a
    JSON schema to the Gemini API (response_schema + response_mime_type).
    If the provider returns malformed JSON, AIErrorKind.MALFORMED_RESPONSE
    is raised.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from app.ai.providers.base import AIProvider
from app.ai.schemas import AIErrorKind, AIMessageInput, AIProviderError, AIResponse, AIUsage

if TYPE_CHECKING:
    from app.ai.schemas import AIRequest

logger = logging.getLogger(__name__)

# Module-level: SDK imported lazily inside generate() to avoid startup failures
_PROVIDER_NAME = "gemini"


def _build_gemini_contents(
    messages: list[AIMessageInput],
) -> list[dict[str, Any]]:
    """Convert AIMessageInput list to Gemini content format.

    Gemini uses {"role": "user"|"model", "parts": [{"text": "..."}]}.
    OpenAI-style "assistant" maps to Gemini "model".
    "system" role messages are handled via system_instruction — skip here.
    """
    contents: list[dict[str, Any]] = []
    for msg in messages:
        if msg.role == "system":
            continue  # handled via system_instruction parameter
        gemini_role = "model" if msg.role == "assistant" else "user"
        contents.append({"role": gemini_role, "parts": [{"text": msg.content}]})
    return contents


class GeminiProvider(AIProvider):
    """Google Gemini provider adapter.

    Configuration (from AIConfig):
        GEMINI_API_KEY  — required when this provider is active.
        GEMINI_MODEL    — model identifier, e.g. "gemini-2.0-flash".
    """

    def __init__(self, api_key: str, model: str) -> None:
        """Initialise the adapter (does NOT make network calls).

        Args:
            api_key: Gemini API key. Not logged; not exposed in responses.
            model:   Gemini model identifier.
        """
        # Store credentials for lazy client creation; never log them.
        self._api_key = api_key
        self._model = model
        self._client: Any = None  # lazily created on first generate()

    @property
    def name(self) -> str:
        return _PROVIDER_NAME

    def _get_client(self) -> Any:
        """Lazily create and cache the Gemini SDK client."""
        if not self._api_key or not self._api_key.strip():
            raise AIProviderError(
                kind=AIErrorKind.AUTH_ERROR,
                provider=self.name,
                message="No Gemini API key was provided. Set GEMINI_API_KEY in .env.",
            )

        if self._client is None:
            try:
                # SDK import is intentionally deferred here.
                from google import genai  # type: ignore[import-untyped]

                self._client = genai.Client(api_key=self._api_key)
            except ImportError as exc:
                raise AIProviderError(
                    kind=AIErrorKind.AUTH_ERROR,
                    provider=self.name,
                    message=(
                        "google-genai SDK is not installed. "
                        "Run: pip install google-genai"
                    ),
                ) from exc
            except Exception as exc:
                raise AIProviderError(
                    kind=AIErrorKind.AUTH_ERROR,
                    provider=self.name,
                    message=_safe_error_message(exc),
                ) from exc
        return self._client

    async def generate(self, request: "AIRequest") -> AIResponse:
        """Call Gemini and return a normalised AIResponse.

        Raises:
            AIProviderError: On any failure (auth, network, quota, …).
        """
        try:
            client = self._get_client()

            # Build content list (system message handled separately)
            contents = _build_gemini_contents(request.messages)

            # If no non-system messages, add the system_prompt as user turn
            if not contents and request.system_prompt:
                contents = [{"role": "user", "parts": [{"text": request.system_prompt}]}]

            # Generation config
            gen_config: dict[str, Any] = {}
            if request.temperature is not None:
                gen_config["temperature"] = request.temperature
            if request.max_tokens is not None:
                gen_config["max_output_tokens"] = request.max_tokens
            if request.response_format:
                gen_config["response_mime_type"] = "application/json"
                # response_schema can be passed as a dict directly
                gen_config["response_schema"] = request.response_format

            model_id = request.model or self._model

            # Lazy import guard already ran via _get_client()
            from google.genai import types as genai_types  # type: ignore[import-untyped]

            config_obj = genai_types.GenerateContentConfig(
                system_instruction=request.system_prompt or None,
                **gen_config,
            )

            response = await client.aio.models.generate_content(
                model=model_id,
                contents=contents,
                config=config_obj,
            )
        except AIProviderError:
            raise
        except Exception as exc:
            kind = _classify_gemini_error(exc)
            raise AIProviderError(
                kind=kind,
                provider=self.name,
                message=_safe_error_message(exc),
            ) from exc

        raw_text: str = ""
        try:
            raw_text = response.text or ""
        except Exception:
            raw_text = ""

        # Parse structured output if requested
        structured: dict[str, Any] | None = None
        if request.response_format and raw_text:
            try:
                structured = json.loads(raw_text)
            except json.JSONDecodeError as exc:
                raise AIProviderError(
                    kind=AIErrorKind.MALFORMED_RESPONSE,
                    provider=self.name,
                    message="Provider returned non-JSON for structured request.",
                ) from exc

        # Usage metadata (best-effort)
        usage = AIUsage()
        try:
            meta = response.usage_metadata
            usage = AIUsage(
                prompt_tokens=getattr(meta, "prompt_token_count", None),
                completion_tokens=getattr(meta, "candidates_token_count", None),
                total_tokens=getattr(meta, "total_token_count", None),
            )
        except Exception:  # noqa: BLE001
            pass

        return AIResponse(
            text=raw_text,
            structured=structured,
            provider=self.name,
            model=model_id,
            usage=usage,
        )


# ---------------------------------------------------------------------------
# Error classification helpers
# ---------------------------------------------------------------------------


def _classify_gemini_error(exc: Exception) -> AIErrorKind:
    """Map a raw Gemini SDK exception to an AIErrorKind."""
    exc_str = str(exc).lower()
    type_name = type(exc).__name__.lower()

    if any(k in exc_str for k in ("api_key", "permission", "unauthori", "403", "401")):
        return AIErrorKind.AUTH_ERROR
    if "429" in exc_str or "quota" in exc_str or "rate" in exc_str:
        return AIErrorKind.RATE_LIMIT
    if "timeout" in exc_str or "timed out" in exc_str or "timeout" in type_name:
        return AIErrorKind.TIMEOUT
    if any(k in exc_str for k in ("503", "502", "unavailable", "connection")):
        return AIErrorKind.PROVIDER_UNAVAILABLE
    if "invalid" in exc_str or "400" in exc_str:
        return AIErrorKind.INVALID_REQUEST
    return AIErrorKind.UNEXPECTED_ERROR


def _safe_error_message(exc: Exception) -> str:
    """Return a sanitised error string that never contains API keys."""
    msg = str(exc)
    # Strip anything that looks like a key (long alphanumeric token)
    import re

    msg = re.sub(r"[A-Za-z0-9_\-]{30,}", "[REDACTED]", msg)
    return msg[:500]  # cap length
