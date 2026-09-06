"""OpenAI provider adapter for Clinova.

SDK dependency: openai >= 1.0.0
    Install: pip install openai

ISOLATION RULE:
    openai SDK imports are CONFINED to this module.
    No other Clinova module may import openai directly.

Lazy initialisation:
    The SDK client is created on the first call to generate().
    Application startup does NOT require OPENAI_API_KEY to be set
    unless OpenAI is the selected provider for an active task.

Structured output:
    When request.response_format is provided, the adapter uses
    the OpenAI response_format parameter with json_schema type.
    If the provider returns invalid JSON, AIErrorKind.MALFORMED_RESPONSE
    is raised.

Compatible providers (OpenAI-compatible API):
    This adapter works with any OpenAI-API-compatible provider by
    overriding the base_url:
        - OpenAI (api.openai.com)
        - Groq (api.groq.com/openai/v1)
        - OpenRouter (openrouter.ai/api/v1)
        - Cerebras (api.cerebras.ai/v1)
    Set OPENAI_BASE_URL in config to point to a compatible endpoint.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from app.ai.providers.base import AIProvider
from app.ai.schemas import AIErrorKind, AIProviderError, AIResponse, AIUsage

if TYPE_CHECKING:
    from app.ai.schemas import AIRequest

logger = logging.getLogger(__name__)

_PROVIDER_NAME = "openai"


class OpenAIProvider(AIProvider):
    """OpenAI (and compatible) provider adapter.

    Configuration (from AIConfig):
        OPENAI_API_KEY  — required when this provider is active.
        OPENAI_MODEL    — model identifier, e.g. "gpt-4o-mini".
        OPENAI_BASE_URL — optional; override for compatible providers
                          (Groq, OpenRouter, Cerebras, etc.).
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str | None = None,
        provider_name: str = _PROVIDER_NAME,
    ) -> None:
        """Initialise the adapter (does NOT make network calls).

        Args:
            api_key:       OpenAI API key. Not logged; not exposed.
            model:         Model identifier.
            base_url:      Optional base URL for OpenAI-compatible endpoints.
            provider_name: Logical name (e.g. 'openai', 'groq', 'openrouter').
        """
        self._api_key = api_key
        self._model = model
        self._base_url = base_url
        self._provider_name = provider_name
        self._client: Any = None  # lazily created

    @property
    def name(self) -> str:
        return self._provider_name

    def _get_client(self) -> Any:
        """Lazily create and cache the OpenAI async client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI  # type: ignore[import-untyped]

                kwargs: dict[str, Any] = {"api_key": self._api_key}
                if self._base_url:
                    kwargs["base_url"] = self._base_url
                self._client = AsyncOpenAI(**kwargs)
            except ImportError as exc:
                raise AIProviderError(
                    kind=AIErrorKind.AUTH_ERROR,
                    provider=self.name,
                    message=(
                        "openai SDK is not installed. "
                        "Run: pip install openai"
                    ),
                ) from exc
        return self._client

    async def generate(self, request: "AIRequest") -> AIResponse:
        """Call OpenAI chat completions and return a normalised AIResponse.

        Raises:
            AIProviderError: On any failure (auth, network, quota, …).
        """
        client = self._get_client()

        # Build messages list
        messages: list[dict[str, str]] = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})

        # If no messages at all, use system_prompt as user turn
        if not messages:
            messages = [{"role": "user", "content": "Hello"}]

        model_id = request.model or self._model

        # Build kwargs
        kwargs: dict[str, Any] = {
            "model": model_id,
            "messages": messages,
        }
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.max_tokens is not None:
            kwargs["max_tokens"] = request.max_tokens

        # Structured output via JSON schema
        if request.response_format:
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "clinova_response",
                    "schema": request.response_format,
                    "strict": True,
                },
            }

        try:
            response = await client.chat.completions.create(**kwargs)
        except Exception as exc:
            kind = _classify_openai_error(exc)
            raise AIProviderError(
                kind=kind,
                provider=self.name,
                message=_safe_error_message(exc),
            ) from exc

        raw_text: str = ""
        try:
            raw_text = response.choices[0].message.content or ""
        except (IndexError, AttributeError):
            raw_text = ""

        # Parse structured output
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

        # Usage
        usage = AIUsage()
        try:
            u = response.usage
            usage = AIUsage(
                prompt_tokens=u.prompt_tokens,
                completion_tokens=u.completion_tokens,
                total_tokens=u.total_tokens,
            )
        except Exception:  # noqa: BLE001
            pass

        actual_model: str = model_id
        try:
            actual_model = response.model or model_id
        except Exception:  # noqa: BLE001
            pass

        return AIResponse(
            text=raw_text,
            structured=structured,
            provider=self.name,
            model=actual_model,
            usage=usage,
        )


# ---------------------------------------------------------------------------
# Error classification helpers
# ---------------------------------------------------------------------------


def _classify_openai_error(exc: Exception) -> AIErrorKind:
    """Map a raw OpenAI SDK exception to an AIErrorKind."""
    type_name = type(exc).__name__

    # openai SDK exception class names (without requiring the import)
    if "AuthenticationError" in type_name or "PermissionDeniedError" in type_name:
        return AIErrorKind.AUTH_ERROR
    if "RateLimitError" in type_name:
        return AIErrorKind.RATE_LIMIT
    if "APITimeoutError" in type_name or "Timeout" in type_name:
        return AIErrorKind.TIMEOUT
    if "APIConnectionError" in type_name or "ServiceUnavailableError" in type_name:
        return AIErrorKind.PROVIDER_UNAVAILABLE
    if "BadRequestError" in type_name or "UnprocessableEntityError" in type_name:
        return AIErrorKind.INVALID_REQUEST
    if "APIStatusError" in type_name:
        exc_str = str(exc)
        if "401" in exc_str or "403" in exc_str:
            return AIErrorKind.AUTH_ERROR
        if "429" in exc_str:
            return AIErrorKind.RATE_LIMIT
        if "503" in exc_str or "502" in exc_str:
            return AIErrorKind.PROVIDER_UNAVAILABLE
    return AIErrorKind.UNEXPECTED_ERROR


def _safe_error_message(exc: Exception) -> str:
    """Return a sanitised error string that never contains API keys."""
    import re

    msg = str(exc)
    msg = re.sub(r"[A-Za-z0-9_\-]{30,}", "[REDACTED]", msg)
    return msg[:500]
