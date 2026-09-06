"""Ollama local provider adapter for Clinova.

No separate SDK required — uses httpx (already in requirements.txt)
to communicate with the Ollama REST API.

ISOLATION RULE:
    httpx is used only here for Ollama. No Ollama-specific types
    leak outside this module.

Lazy initialisation:
    No connection is made at class instantiation or application startup.
    Ollama is only contacted when generate() is called.

API:
    POST {base_url}/api/chat

Configuration (from AIConfig):
    OLLAMA_BASE_URL  — defaults to http://localhost:11434
    OLLAMA_MODEL     — e.g. "llama3.2", "mistral", "gemma3"

Structured output:
    Ollama supports "format": "json" for JSON mode.
    When request.response_format is provided, json mode is enabled
    and the response text is parsed. If parsing fails,
    AIErrorKind.MALFORMED_RESPONSE is raised.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

import httpx

from app.ai.providers.base import AIProvider
from app.ai.schemas import AIErrorKind, AIProviderError, AIResponse, AIUsage

if TYPE_CHECKING:
    from app.ai.schemas import AIRequest

logger = logging.getLogger(__name__)

_PROVIDER_NAME = "ollama"
_DEFAULT_BASE_URL = "http://localhost:11434"
_REQUEST_TIMEOUT = 120.0  # seconds — local models can be slow on first load


def _build_ollama_messages(request: "AIRequest") -> list[dict[str, str]]:
    """Build Ollama /api/chat messages list.

    Ollama uses OpenAI-compatible message format:
        {"role": "system"|"user"|"assistant", "content": "..."}
    """
    messages: list[dict[str, str]] = []
    if request.system_prompt:
        messages.append({"role": "system", "content": request.system_prompt})
    for msg in request.messages:
        messages.append({"role": msg.role, "content": msg.content})
    if not messages:
        messages = [{"role": "user", "content": "Hello"}]
    return messages


class OllamaProvider(AIProvider):
    """Ollama local inference provider adapter.

    Communicates with the Ollama REST API using httpx.
    Does NOT require Ollama to be running at startup.
    """

    def __init__(self, base_url: str = _DEFAULT_BASE_URL, model: str = "llama3.2") -> None:
        """Initialise the adapter (does NOT connect to Ollama).

        Args:
            base_url: Ollama server URL (default http://localhost:11434).
            model:    Ollama model name, e.g. 'llama3.2', 'mistral'.
        """
        self._base_url = base_url.rstrip("/")
        self._model = model

    @property
    def name(self) -> str:
        return _PROVIDER_NAME

    async def generate(self, request: "AIRequest") -> AIResponse:
        """Send a chat request to Ollama and return a normalised AIResponse.

        Raises:
            AIProviderError: On connection failure, timeout, bad response, etc.
        """
        model_id = request.model or self._model
        messages = _build_ollama_messages(request)

        payload: dict[str, Any] = {
            "model": model_id,
            "messages": messages,
            "stream": False,
        }

        if request.temperature is not None:
            payload["options"] = payload.get("options", {})
            payload["options"]["temperature"] = request.temperature

        if request.max_tokens is not None:
            payload["options"] = payload.get("options", {})
            payload["options"]["num_predict"] = request.max_tokens

        # JSON mode for structured output
        if request.response_format:
            payload["format"] = "json"

        url = f"{self._base_url}/api/chat"

        try:
            async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
        except httpx.ConnectError as exc:
            raise AIProviderError(
                kind=AIErrorKind.PROVIDER_UNAVAILABLE,
                provider=self.name,
                message=(
                    f"Cannot connect to Ollama at {self._base_url}. "
                    "Ensure Ollama is running: 'ollama serve'."
                ),
            ) from exc
        except httpx.TimeoutException as exc:
            raise AIProviderError(
                kind=AIErrorKind.TIMEOUT,
                provider=self.name,
                message=f"Ollama request timed out after {_REQUEST_TIMEOUT}s.",
            ) from exc
        except httpx.HTTPStatusError as exc:
            kind = _classify_ollama_http_error(exc.response.status_code)
            raise AIProviderError(
                kind=kind,
                provider=self.name,
                message=f"Ollama returned HTTP {exc.response.status_code}.",
            ) from exc
        except httpx.RequestError as exc:
            raise AIProviderError(
                kind=AIErrorKind.PROVIDER_UNAVAILABLE,
                provider=self.name,
                message=f"Ollama request error: {type(exc).__name__}",
            ) from exc

        # Parse response
        try:
            data: dict[str, Any] = resp.json()
        except Exception as exc:
            raise AIProviderError(
                kind=AIErrorKind.MALFORMED_RESPONSE,
                provider=self.name,
                message="Ollama returned non-JSON response body.",
            ) from exc

        raw_text: str = ""
        try:
            raw_text = data["message"]["content"] or ""
        except (KeyError, TypeError) as exc:
            raise AIProviderError(
                kind=AIErrorKind.MALFORMED_RESPONSE,
                provider=self.name,
                message="Ollama response missing expected 'message.content' field.",
            ) from exc

        # Parse structured output
        structured: dict[str, Any] | None = None
        if request.response_format and raw_text:
            try:
                structured = json.loads(raw_text)
            except json.JSONDecodeError as exc:
                raise AIProviderError(
                    kind=AIErrorKind.MALFORMED_RESPONSE,
                    provider=self.name,
                    message="Ollama returned non-JSON content for structured request.",
                ) from exc

        # Usage (Ollama provides eval_count / prompt_eval_count)
        usage = AIUsage(
            prompt_tokens=data.get("prompt_eval_count"),
            completion_tokens=data.get("eval_count"),
        )
        if usage.prompt_tokens is not None and usage.completion_tokens is not None:
            usage.total_tokens = usage.prompt_tokens + usage.completion_tokens

        return AIResponse(
            text=raw_text,
            structured=structured,
            provider=self.name,
            model=data.get("model", model_id),
            usage=usage,
            metadata={"done": data.get("done", False)},
        )


def _classify_ollama_http_error(status_code: int) -> AIErrorKind:
    """Map Ollama HTTP status codes to AIErrorKind."""
    if status_code in (401, 403):
        return AIErrorKind.AUTH_ERROR
    if status_code == 429:
        return AIErrorKind.RATE_LIMIT
    if status_code in (400, 422):
        return AIErrorKind.INVALID_REQUEST
    if status_code in (502, 503, 504):
        return AIErrorKind.PROVIDER_UNAVAILABLE
    return AIErrorKind.UNEXPECTED_ERROR
