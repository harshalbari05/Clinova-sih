"""Provider-independent AI schemas for Clinova.

These dataclasses/enums define the contract between application code
and the AI provider layer. No provider SDK types appear here.

Classes:
    AIErrorKind      — Enum of error categories.
    AIProviderError  — Exception raised by providers (carries AIErrorKind).
    AIMessageInput   — A single conversation turn (role + content).
    AIRequest        — Full provider-agnostic inference request.
    AIResponse       — Normalised provider response returned to callers.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Error taxonomy
# ---------------------------------------------------------------------------


class AIErrorKind(str, enum.Enum):
    """Categorises provider errors so callers can react appropriately.

    AUTH_ERROR          — Missing or invalid API key / credentials.
                          Do NOT retry; operator action required.
    INVALID_REQUEST     — The request itself is malformed or rejected.
                          Do NOT retry without changing the request.
    PROVIDER_UNAVAILABLE — Provider endpoint is unreachable or down.
                          May retry with fallback or later.
    RATE_LIMIT          — Provider quota exhausted.
                          May retry with a fallback provider.
    TIMEOUT             — Request exceeded time limit.
                          May retry with fallback or same provider.
    MALFORMED_RESPONSE  — Provider returned an unexpected response shape.
                          Log and surface; do not retry blindly.
    UNEXPECTED_ERROR    — Catch-all for unforeseen provider exceptions.
    """

    AUTH_ERROR = "auth_error"
    INVALID_REQUEST = "invalid_request"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    MALFORMED_RESPONSE = "malformed_response"
    UNEXPECTED_ERROR = "unexpected_error"


class AIProviderError(Exception):
    """Raised by provider adapters to signal structured failure.

    Attributes:
        kind:     The error category (AIErrorKind).
        provider: Name of the provider that raised the error.
        message:  Human-readable description (safe to log — no secrets).
        retryable: Whether a fallback/retry attempt makes sense.
    """

    # Error kinds that should NOT be retried (misconfiguration / bad request)
    _NON_RETRYABLE: frozenset[AIErrorKind] = frozenset(
        {AIErrorKind.AUTH_ERROR, AIErrorKind.INVALID_REQUEST}
    )

    def __init__(
        self,
        kind: AIErrorKind,
        provider: str,
        message: str,
    ) -> None:
        super().__init__(message)
        self.kind = kind
        self.provider = provider
        self.message = message

    @property
    def retryable(self) -> bool:
        """True if a fallback provider or later retry may succeed."""
        return self.kind not in self._NON_RETRYABLE

    def __repr__(self) -> str:
        return (
            f"AIProviderError(kind={self.kind!r}, "
            f"provider={self.provider!r}, "
            f"message={self.message!r})"
        )


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


@dataclass
class AIMessageInput:
    """A single conversation turn passed to the provider.

    role:    "system" | "user" | "assistant"
    content: Text content of the turn.
    """

    role: str
    content: str


@dataclass
class AIRequest:
    """Provider-agnostic inference request.

    Fields that are not supported by a specific provider are
    silently ignored by that provider's adapter.

    Attributes:
        messages:         Ordered conversation history (role/content pairs).
        system_prompt:    Optional system instruction (separate from messages).
        model:            Provider-specific model identifier. If None, the
                          provider uses its configured default.
        temperature:      Sampling temperature (0.0–2.0). Provider-ignored if
                          not supported.
        max_tokens:       Maximum tokens in the completion.
        response_format:  Optional JSON schema dict for structured output.
                          Providers that don't support structured output will
                          ignore this field; callers should handle plain text.
        metadata:         Arbitrary key/value data forwarded to the provider
                          adapter for tracing or logging (never sent to the
                          model itself).
    """

    messages: list[AIMessageInput] = field(default_factory=list)
    system_prompt: str | None = None
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    response_format: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


@dataclass
class AIUsage:
    """Token usage reported by the provider (where available)."""

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


@dataclass
class AIResponse:
    """Normalised inference response returned by all provider adapters.

    Attributes:
        text:       Raw text output from the model.
        structured: Parsed JSON dict if the request used response_format
                    and the provider returned valid structured output.
                    None otherwise.
        provider:   Name of the provider that served the request.
        model:      Specific model identifier returned by the provider.
        usage:      Token usage (prompt / completion / total).
        metadata:   Provider-specific metadata (safe to log — no secrets).
    """

    text: str
    provider: str
    model: str
    structured: dict[str, Any] | None = None
    usage: AIUsage = field(default_factory=AIUsage)
    metadata: dict[str, Any] = field(default_factory=dict)
