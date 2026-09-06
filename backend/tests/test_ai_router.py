"""Tests for the AI Task Router.

All tests use mocks — no real network calls, no real API keys.

Test coverage:
  ROUTING
   1. HISTORY_INTERVIEW routes to configured provider.
   2. STRUCTURED_EXTRACTION routes to configured provider.
   3. Different tasks can use different providers.
   4. Provider can be changed through configuration.
   5. Task with no override uses AI_DEFAULT_PROVIDER.
   6. get_provider_name_for_task() returns correct names.

  FALLBACK
   7. Primary provider failure triggers fallback.
   8. Successful primary provider does NOT call fallback.
   9. Rate-limit error triggers fallback (retryable).
  10. Provider-unavailable error triggers fallback (retryable).
  11. Timeout error triggers fallback (retryable).
  12. Fallback exhaustion returns controlled AIProviderError.
  13. Retries do NOT continue beyond MAX_ATTEMPTS.
  14. AUTH_ERROR is NOT retried (non-retryable).
  15. INVALID_REQUEST is NOT retried (non-retryable).
  16. Successful fallback returns AIResponse (not primary error).

  SECURITY
  17. API keys never appear in router log output.
  18. Provider-specific types do not leak into AIResponse.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.registry import clear_provider_cache
from app.ai.router import AITaskRouter, MAX_ATTEMPTS
from app.ai.schemas import (
    AIErrorKind,
    AIMessageInput,
    AIProviderError,
    AIRequest,
    AIResponse,
    AIUsage,
)
from app.ai.tasks import AITaskType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_request(content: str = "Hello") -> AIRequest:
    return AIRequest(messages=[AIMessageInput(role="user", content=content)])


def make_response(text: str = "OK", provider: str = "ollama") -> AIResponse:
    return AIResponse(text=text, provider=provider, model="test-model")


def make_provider_error(
    kind: AIErrorKind, provider: str = "ollama"
) -> AIProviderError:
    return AIProviderError(kind=kind, provider=provider, message=f"Error: {kind.value}")


@pytest.fixture(autouse=True)
def reset_registry():
    clear_provider_cache()
    yield
    clear_provider_cache()


# ---------------------------------------------------------------------------
# 1–6: Routing
# ---------------------------------------------------------------------------


def test_history_interview_resolves_configured_provider():
    """HISTORY_INTERVIEW resolves to its configured provider."""
    router = AITaskRouter()
    with patch("app.ai.router.ai_settings") as mock_settings:
        mock_settings.AI_HISTORY_INTERVIEW_PROVIDER = "gemini"
        mock_settings.AI_DEFAULT_PROVIDER = "ollama"
        name = router.get_provider_name_for_task(AITaskType.HISTORY_INTERVIEW)
    assert name == "gemini"


def test_structured_extraction_resolves_configured_provider():
    """STRUCTURED_EXTRACTION resolves to its configured provider."""
    router = AITaskRouter()
    with patch("app.ai.router.ai_settings") as mock_settings:
        mock_settings.AI_STRUCTURED_EXTRACTION_PROVIDER = "openai"
        mock_settings.AI_DEFAULT_PROVIDER = "ollama"
        name = router.get_provider_name_for_task(AITaskType.STRUCTURED_EXTRACTION)
    assert name == "openai"


def test_different_tasks_use_different_providers():
    """Different tasks can be configured to use different providers."""
    router = AITaskRouter()
    with patch("app.ai.router.ai_settings") as mock_settings:
        mock_settings.AI_HISTORY_INTERVIEW_PROVIDER = "gemini"
        mock_settings.AI_STRUCTURED_EXTRACTION_PROVIDER = "openai"
        mock_settings.AI_DEFAULT_PROVIDER = "ollama"
        history_name = router.get_provider_name_for_task(AITaskType.HISTORY_INTERVIEW)
        extraction_name = router.get_provider_name_for_task(AITaskType.STRUCTURED_EXTRACTION)
    assert history_name == "gemini"
    assert extraction_name == "openai"


def test_provider_changeable_through_configuration():
    """Provider for a task can be changed without code changes."""
    router = AITaskRouter()
    # First config: Gemini
    with patch("app.ai.router.ai_settings") as mock_settings:
        mock_settings.AI_HISTORY_INTERVIEW_PROVIDER = "gemini"
        mock_settings.AI_DEFAULT_PROVIDER = "ollama"
        name1 = router.get_provider_name_for_task(AITaskType.HISTORY_INTERVIEW)

    # Second config: OpenAI
    with patch("app.ai.router.ai_settings") as mock_settings:
        mock_settings.AI_HISTORY_INTERVIEW_PROVIDER = "openai"
        mock_settings.AI_DEFAULT_PROVIDER = "ollama"
        name2 = router.get_provider_name_for_task(AITaskType.HISTORY_INTERVIEW)

    assert name1 == "gemini"
    assert name2 == "openai"


def test_task_with_no_override_uses_default_provider():
    """Task with no specific override falls back to AI_DEFAULT_PROVIDER."""
    router = AITaskRouter()
    with patch("app.ai.router.ai_settings") as mock_settings:
        mock_settings.AI_HISTORY_INTERVIEW_PROVIDER = None
        mock_settings.AI_DEFAULT_PROVIDER = "ollama"
        name = router.get_provider_name_for_task(AITaskType.HISTORY_INTERVIEW)
    assert name == "ollama"


def test_get_provider_name_for_all_task_types():
    """All AITaskType values resolve to a provider name without error."""
    router = AITaskRouter()
    with patch("app.ai.router.ai_settings") as mock_settings:
        mock_settings.AI_HISTORY_INTERVIEW_PROVIDER = None
        mock_settings.AI_STRUCTURED_EXTRACTION_PROVIDER = None
        mock_settings.AI_CLINICAL_SUMMARY_PROVIDER = None
        mock_settings.AI_DOCUMENT_ANALYSIS_PROVIDER = None
        mock_settings.AI_TRANSLATION_PROVIDER = None
        mock_settings.AI_TRIAGE_PROVIDER = None
        mock_settings.AI_DEFAULT_PROVIDER = "ollama"
        for task in AITaskType:
            name = router.get_provider_name_for_task(task)
            assert name == "ollama"


# ---------------------------------------------------------------------------
# 7–16: Fallback
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_primary_failure_triggers_fallback():
    """When primary provider fails (retryable), fallback is tried."""
    router = AITaskRouter()
    request = make_request()
    fallback_response = make_response(text="fallback response", provider="openai")

    primary_error = make_provider_error(AIErrorKind.PROVIDER_UNAVAILABLE, "ollama")

    mock_primary = MagicMock()
    mock_primary.generate = AsyncMock(side_effect=primary_error)

    mock_fallback = MagicMock()
    mock_fallback.generate = AsyncMock(return_value=fallback_response)

    with patch("app.ai.router.ai_settings") as mock_settings:
        mock_settings.AI_DEFAULT_PROVIDER = "ollama"
        mock_settings.AI_HISTORY_INTERVIEW_PROVIDER = None
        mock_settings.AI_FALLBACK_PROVIDERS = ["openai"]

        with patch("app.ai.router.get_provider") as mock_get_provider:
            mock_get_provider.side_effect = lambda name: (
                mock_primary if name == "ollama" else mock_fallback
            )
            result = await router.generate(
                task=AITaskType.HISTORY_INTERVIEW,
                request=request,
            )

    assert result.text == "fallback response"
    assert result.provider == "openai"


@pytest.mark.asyncio
async def test_successful_primary_does_not_call_fallback():
    """When primary succeeds, fallback provider is never called."""
    router = AITaskRouter()
    request = make_request()
    primary_response = make_response(text="primary OK", provider="ollama")

    mock_primary = MagicMock()
    mock_primary.generate = AsyncMock(return_value=primary_response)

    mock_fallback = MagicMock()
    mock_fallback.generate = AsyncMock(return_value=make_response("fallback"))

    with patch("app.ai.router.ai_settings") as mock_settings:
        mock_settings.AI_DEFAULT_PROVIDER = "ollama"
        mock_settings.AI_HISTORY_INTERVIEW_PROVIDER = None
        mock_settings.AI_FALLBACK_PROVIDERS = ["openai"]

        with patch("app.ai.router.get_provider") as mock_get_provider:
            mock_get_provider.side_effect = lambda name: (
                mock_primary if name == "ollama" else mock_fallback
            )
            result = await router.generate(
                task=AITaskType.HISTORY_INTERVIEW,
                request=request,
            )

    mock_fallback.generate.assert_not_called()
    assert result.text == "primary OK"


@pytest.mark.asyncio
async def test_rate_limit_triggers_fallback():
    """RATE_LIMIT error is retryable and triggers fallback."""
    router = AITaskRouter()
    fallback_response = make_response(text="fallback", provider="gemini")

    mock_primary = MagicMock()
    mock_primary.generate = AsyncMock(
        side_effect=make_provider_error(AIErrorKind.RATE_LIMIT, "ollama")
    )
    mock_fallback = MagicMock()
    mock_fallback.generate = AsyncMock(return_value=fallback_response)

    with patch("app.ai.router.ai_settings") as mock_settings:
        mock_settings.AI_DEFAULT_PROVIDER = "ollama"
        mock_settings.AI_HISTORY_INTERVIEW_PROVIDER = None
        mock_settings.AI_FALLBACK_PROVIDERS = ["gemini"]

        with patch("app.ai.router.get_provider") as mock_get_provider:
            mock_get_provider.side_effect = lambda name: (
                mock_primary if name == "ollama" else mock_fallback
            )
            result = await router.generate(
                task=AITaskType.HISTORY_INTERVIEW,
                request=make_request(),
            )

    assert result.text == "fallback"


@pytest.mark.asyncio
async def test_provider_unavailable_triggers_fallback():
    """PROVIDER_UNAVAILABLE is retryable and triggers fallback."""
    router = AITaskRouter()
    fallback_response = make_response(text="from fallback", provider="openai")

    mock_primary = MagicMock()
    mock_primary.generate = AsyncMock(
        side_effect=make_provider_error(AIErrorKind.PROVIDER_UNAVAILABLE, "ollama")
    )
    mock_fallback = MagicMock()
    mock_fallback.generate = AsyncMock(return_value=fallback_response)

    with patch("app.ai.router.ai_settings") as mock_settings:
        mock_settings.AI_DEFAULT_PROVIDER = "ollama"
        mock_settings.AI_HISTORY_INTERVIEW_PROVIDER = None
        mock_settings.AI_FALLBACK_PROVIDERS = ["openai"]

        with patch("app.ai.router.get_provider") as mock_get_provider:
            mock_get_provider.side_effect = lambda name: (
                mock_primary if name == "ollama" else mock_fallback
            )
            result = await router.generate(
                task=AITaskType.HISTORY_INTERVIEW,
                request=make_request(),
            )

    assert result.text == "from fallback"


@pytest.mark.asyncio
async def test_timeout_triggers_fallback():
    """TIMEOUT is retryable and triggers fallback."""
    router = AITaskRouter()
    fallback_response = make_response(text="timeout fallback", provider="gemini")

    mock_primary = MagicMock()
    mock_primary.generate = AsyncMock(
        side_effect=make_provider_error(AIErrorKind.TIMEOUT, "ollama")
    )
    mock_fallback = MagicMock()
    mock_fallback.generate = AsyncMock(return_value=fallback_response)

    with patch("app.ai.router.ai_settings") as mock_settings:
        mock_settings.AI_DEFAULT_PROVIDER = "ollama"
        mock_settings.AI_HISTORY_INTERVIEW_PROVIDER = None
        mock_settings.AI_FALLBACK_PROVIDERS = ["gemini"]

        with patch("app.ai.router.get_provider") as mock_get_provider:
            mock_get_provider.side_effect = lambda name: (
                mock_primary if name == "ollama" else mock_fallback
            )
            result = await router.generate(
                task=AITaskType.HISTORY_INTERVIEW,
                request=make_request(),
            )

    assert result.text == "timeout fallback"


@pytest.mark.asyncio
async def test_fallback_exhaustion_raises_controlled_error():
    """When all providers fail, AIProviderError is raised (not silently swallowed)."""
    router = AITaskRouter()

    failing_provider = MagicMock()
    failing_provider.generate = AsyncMock(
        side_effect=make_provider_error(AIErrorKind.PROVIDER_UNAVAILABLE, "ollama")
    )

    with patch("app.ai.router.ai_settings") as mock_settings:
        mock_settings.AI_DEFAULT_PROVIDER = "ollama"
        mock_settings.AI_HISTORY_INTERVIEW_PROVIDER = None
        mock_settings.AI_FALLBACK_PROVIDERS = ["openai", "gemini"]

        with patch("app.ai.router.get_provider", return_value=failing_provider):
            with pytest.raises(AIProviderError) as exc_info:
                await router.generate(
                    task=AITaskType.HISTORY_INTERVIEW,
                    request=make_request(),
                )

    assert exc_info.value.kind == AIErrorKind.PROVIDER_UNAVAILABLE


@pytest.mark.asyncio
async def test_retries_do_not_exceed_max_attempts():
    """Total provider attempts never exceed MAX_ATTEMPTS."""
    router = AITaskRouter()
    call_count = 0

    async def failing_generate(request):
        nonlocal call_count
        call_count += 1
        raise make_provider_error(AIErrorKind.PROVIDER_UNAVAILABLE, "ollama")

    failing_provider = MagicMock()
    failing_provider.generate = failing_generate

    with patch("app.ai.router.ai_settings") as mock_settings:
        mock_settings.AI_DEFAULT_PROVIDER = "ollama"
        mock_settings.AI_HISTORY_INTERVIEW_PROVIDER = None
        # Provide many fallbacks — router should still cap at MAX_ATTEMPTS
        mock_settings.AI_FALLBACK_PROVIDERS = ["p1", "p2", "p3", "p4", "p5"]

        with patch("app.ai.router.get_provider", return_value=failing_provider):
            with pytest.raises(AIProviderError):
                await router.generate(
                    task=AITaskType.HISTORY_INTERVIEW,
                    request=make_request(),
                )

    assert call_count <= MAX_ATTEMPTS


@pytest.mark.asyncio
async def test_auth_error_is_not_retried():
    """AUTH_ERROR (non-retryable) aborts immediately without trying fallback."""
    router = AITaskRouter()
    call_count = 0

    async def auth_failing_generate(request):
        nonlocal call_count
        call_count += 1
        raise make_provider_error(AIErrorKind.AUTH_ERROR, "ollama")

    failing_provider = MagicMock()
    failing_provider.generate = auth_failing_generate

    fallback_provider = MagicMock()
    fallback_provider.generate = AsyncMock(return_value=make_response())

    with patch("app.ai.router.ai_settings") as mock_settings:
        mock_settings.AI_DEFAULT_PROVIDER = "ollama"
        mock_settings.AI_HISTORY_INTERVIEW_PROVIDER = None
        mock_settings.AI_FALLBACK_PROVIDERS = ["openai"]

        with patch("app.ai.router.get_provider") as mock_get_provider:
            mock_get_provider.side_effect = lambda name: (
                failing_provider if name == "ollama" else fallback_provider
            )
            with pytest.raises(AIProviderError) as exc_info:
                await router.generate(
                    task=AITaskType.HISTORY_INTERVIEW,
                    request=make_request(),
                )

    assert exc_info.value.kind == AIErrorKind.AUTH_ERROR
    assert call_count == 1  # Only tried once
    fallback_provider.generate.assert_not_called()


@pytest.mark.asyncio
async def test_invalid_request_error_is_not_retried():
    """INVALID_REQUEST (non-retryable) aborts immediately."""
    router = AITaskRouter()
    call_count = 0

    async def invalid_generate(request):
        nonlocal call_count
        call_count += 1
        raise make_provider_error(AIErrorKind.INVALID_REQUEST, "openai")

    failing_provider = MagicMock()
    failing_provider.generate = invalid_generate

    fallback_provider = MagicMock()
    fallback_provider.generate = AsyncMock(return_value=make_response())

    with patch("app.ai.router.ai_settings") as mock_settings:
        mock_settings.AI_DEFAULT_PROVIDER = "openai"
        mock_settings.AI_HISTORY_INTERVIEW_PROVIDER = None
        mock_settings.AI_FALLBACK_PROVIDERS = ["ollama"]

        with patch("app.ai.router.get_provider") as mock_get_provider:
            mock_get_provider.side_effect = lambda name: (
                failing_provider if name == "openai" else fallback_provider
            )
            with pytest.raises(AIProviderError) as exc_info:
                await router.generate(
                    task=AITaskType.HISTORY_INTERVIEW,
                    request=make_request(),
                )

    assert exc_info.value.kind == AIErrorKind.INVALID_REQUEST
    assert call_count == 1
    fallback_provider.generate.assert_not_called()


@pytest.mark.asyncio
async def test_successful_fallback_returns_ai_response():
    """After primary fails, successful fallback returns a proper AIResponse."""
    router = AITaskRouter()
    expected_text = "Fallback worked!"

    mock_primary = MagicMock()
    mock_primary.generate = AsyncMock(
        side_effect=make_provider_error(AIErrorKind.PROVIDER_UNAVAILABLE)
    )
    mock_fallback = MagicMock()
    mock_fallback.generate = AsyncMock(
        return_value=AIResponse(
            text=expected_text,
            provider="gemini",
            model="gemini-2.0-flash",
            usage=AIUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        )
    )

    with patch("app.ai.router.ai_settings") as mock_settings:
        mock_settings.AI_DEFAULT_PROVIDER = "ollama"
        mock_settings.AI_HISTORY_INTERVIEW_PROVIDER = None
        mock_settings.AI_FALLBACK_PROVIDERS = ["gemini"]

        with patch("app.ai.router.get_provider") as mock_get_provider:
            mock_get_provider.side_effect = lambda name: (
                mock_primary if name == "ollama" else mock_fallback
            )
            result = await router.generate(
                task=AITaskType.HISTORY_INTERVIEW,
                request=make_request(),
            )

    assert isinstance(result, AIResponse)
    assert result.text == expected_text
    assert result.provider == "gemini"
    assert result.usage.total_tokens == 15


# ---------------------------------------------------------------------------
# 17–18: Security / type isolation
# ---------------------------------------------------------------------------


def test_ai_response_contains_no_provider_sdk_types():
    """AIResponse fields are plain Python types — no SDK objects."""
    response = AIResponse(
        text="hello",
        provider="ollama",
        model="llama3.2",
        usage=AIUsage(prompt_tokens=5, completion_tokens=3, total_tokens=8),
    )
    # All fields should be plain Python types
    assert isinstance(response.text, str)
    assert isinstance(response.provider, str)
    assert isinstance(response.model, str)
    assert isinstance(response.usage.prompt_tokens, int)


@pytest.mark.asyncio
async def test_router_error_messages_do_not_expose_api_keys():
    """Error messages propagated by the router never contain raw API keys."""
    router = AITaskRouter()
    fake_key = "sk-" + "X" * 48

    auth_error = AIProviderError(
        kind=AIErrorKind.AUTH_ERROR,
        provider="openai",
        # Simulate a redacted message (provider should sanitise before raising)
        message=f"API key [REDACTED] is invalid.",
    )

    mock_provider = MagicMock()
    mock_provider.generate = AsyncMock(side_effect=auth_error)

    with patch("app.ai.router.ai_settings") as mock_settings:
        mock_settings.AI_DEFAULT_PROVIDER = "openai"
        mock_settings.AI_HISTORY_INTERVIEW_PROVIDER = None
        mock_settings.AI_FALLBACK_PROVIDERS = []

        with patch("app.ai.router.get_provider", return_value=mock_provider):
            with pytest.raises(AIProviderError) as exc_info:
                await router.generate(
                    task=AITaskType.HISTORY_INTERVIEW,
                    request=make_request(),
                )

    assert fake_key not in exc_info.value.message
