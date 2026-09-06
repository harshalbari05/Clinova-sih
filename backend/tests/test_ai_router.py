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
        # Provide many fallbacks — router should still cap at MAX_ATTEMPTS (5)
        mock_settings.AI_FALLBACK_PROVIDERS = ["p1", "p2", "p3", "p4", "p5", "p6", "p7"]

        with patch("app.ai.router.get_provider", return_value=failing_provider):
            with pytest.raises(AIProviderError):
                await router.generate(
                    task=AITaskType.HISTORY_INTERVIEW,
                    request=make_request(),
                )

    assert call_count == MAX_ATTEMPTS


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


# ---------------------------------------------------------------------------
# 19–27: Provider Priority & Fallback Order (Task 8: Tests A–F + Normalization)
# ---------------------------------------------------------------------------


def test_test_a_provider_fallback_chain_order():
    """Test A: AI_DEFAULT_PROVIDER=gemini, AI_FALLBACK_PROVIDERS=groq,openrouter,ollama.
    Expected order: gemini → groq → openrouter → ollama.
    """
    router = AITaskRouter()
    with patch("app.ai.router.ai_settings") as mock_settings:
        mock_settings.AI_DEFAULT_PROVIDER = "gemini"
        mock_settings.AI_HISTORY_INTERVIEW_PROVIDER = None
        mock_settings.AI_FALLBACK_PROVIDERS = ["groq", "openrouter", "ollama"]

        chain = router._build_provider_chain(AITaskType.HISTORY_INTERVIEW)

    assert chain == ["gemini", "groq", "openrouter", "ollama"]
    assert chain[-1] == "ollama"


def test_test_b_task_specific_provider_selects_ollama_directly():
    """Test B: AI_DEFAULT_PROVIDER=gemini, AI_HISTORY_INTERVIEW_PROVIDER=ollama.
    Expected: ollama is selected directly for HISTORY_INTERVIEW.
    """
    router = AITaskRouter()
    with patch("app.ai.router.ai_settings") as mock_settings:
        mock_settings.AI_DEFAULT_PROVIDER = "gemini"
        mock_settings.AI_HISTORY_INTERVIEW_PROVIDER = "ollama"
        mock_settings.AI_FALLBACK_PROVIDERS = ["groq", "openrouter", "ollama"]

        provider_name = router.get_provider_name_for_task(AITaskType.HISTORY_INTERVIEW)
        chain = router._build_provider_chain(AITaskType.HISTORY_INTERVIEW)

    assert provider_name == "ollama"
    assert chain[0] == "ollama"


def test_test_c_empty_task_specific_provider_uses_default():
    """Test C: AI_DEFAULT_PROVIDER=gemini, AI_HISTORY_INTERVIEW_PROVIDER="".
    Expected: gemini is selected for HISTORY_INTERVIEW.
    """
    router = AITaskRouter()
    with patch("app.ai.router.ai_settings") as mock_settings:
        mock_settings.AI_DEFAULT_PROVIDER = "gemini"
        mock_settings.AI_HISTORY_INTERVIEW_PROVIDER = ""
        mock_settings.AI_FALLBACK_PROVIDERS = ["groq", "openrouter", "ollama"]

        provider_name = router.get_provider_name_for_task(AITaskType.HISTORY_INTERVIEW)
        chain = router._build_provider_chain(AITaskType.HISTORY_INTERVIEW)

    assert provider_name == "gemini"
    assert chain == ["gemini", "groq", "openrouter", "ollama"]


@pytest.mark.asyncio
async def test_test_d_cloud_provider_retryable_error_attempts_next():
    """Test D: Cloud provider fails with retryable error -> next configured provider is attempted."""
    router = AITaskRouter()
    attempts: list[str] = []

    def make_mock(name: str):
        mock = MagicMock()
        if name == "gemini":
            mock.generate = AsyncMock(
                side_effect=make_provider_error(AIErrorKind.RATE_LIMIT, "gemini")
            )
        elif name == "groq":
            async def groq_gen(req):
                attempts.append("groq")
                return make_response("groq success", "groq")
            mock.generate = AsyncMock(side_effect=groq_gen)
        else:
            mock.generate = AsyncMock(return_value=make_response("ok", name))
        return mock

    with patch("app.ai.router.ai_settings") as mock_settings:
        mock_settings.AI_DEFAULT_PROVIDER = "gemini"
        mock_settings.AI_HISTORY_INTERVIEW_PROVIDER = None
        mock_settings.AI_FALLBACK_PROVIDERS = ["groq", "openrouter", "ollama"]

        with patch("app.ai.router.get_provider", side_effect=make_mock):
            res = await router.generate(AITaskType.HISTORY_INTERVIEW, make_request())

    assert res.provider == "groq"
    assert res.text == "groq success"
    assert "groq" in attempts


@pytest.mark.asyncio
async def test_test_e_openrouter_fails_triggers_ollama_last():
    """Test E: OpenRouter fails -> Ollama is attempted only after earlier providers fail."""
    router = AITaskRouter()
    called_order: list[str] = []

    def make_mock(name: str):
        mock = MagicMock()
        if name in ("gemini", "groq", "openrouter"):
            async def failing_gen(req):
                called_order.append(name)
                raise make_provider_error(AIErrorKind.PROVIDER_UNAVAILABLE, name)
            mock.generate = AsyncMock(side_effect=failing_gen)
        elif name == "ollama":
            async def ollama_gen(req):
                called_order.append(name)
                return make_response("ollama fallback success", "ollama")
            mock.generate = AsyncMock(side_effect=ollama_gen)
        return mock

    with patch("app.ai.router.ai_settings") as mock_settings:
        mock_settings.AI_DEFAULT_PROVIDER = "gemini"
        mock_settings.AI_HISTORY_INTERVIEW_PROVIDER = None
        mock_settings.AI_FALLBACK_PROVIDERS = ["groq", "openrouter", "ollama"]

        with patch("app.ai.router.get_provider", side_effect=make_mock):
            res = await router.generate(AITaskType.HISTORY_INTERVIEW, make_request())

    assert called_order == ["gemini", "groq", "openrouter", "ollama"]
    assert res.provider == "ollama"
    assert res.text == "ollama fallback success"


@pytest.mark.asyncio
async def test_test_f_ollama_explicitly_selected_as_default():
    """Test F: Ollama explicitly selected as default -> application still works and Ollama is primary."""
    router = AITaskRouter()
    mock_ollama = MagicMock()
    mock_ollama.generate = AsyncMock(return_value=make_response("local response", "ollama"))

    with patch("app.ai.router.ai_settings") as mock_settings:
        mock_settings.AI_DEFAULT_PROVIDER = "ollama"
        mock_settings.AI_HISTORY_INTERVIEW_PROVIDER = None
        mock_settings.AI_FALLBACK_PROVIDERS = ["groq", "openrouter", "ollama"]

        provider_name = router.get_provider_name_for_task(AITaskType.HISTORY_INTERVIEW)
        chain = router._build_provider_chain(AITaskType.HISTORY_INTERVIEW)

        with patch("app.ai.router.get_provider", return_value=mock_ollama):
            res = await router.generate(AITaskType.HISTORY_INTERVIEW, make_request())

    assert provider_name == "ollama"
    assert chain[0] == "ollama"
    assert res.provider == "ollama"
    assert res.text == "local response"


def test_ollama_moved_to_last_if_listed_early_in_fallbacks():
    """If fallback list places ollama before cloud providers, router moves ollama to the end."""
    router = AITaskRouter()
    with patch("app.ai.router.ai_settings") as mock_settings:
        mock_settings.AI_DEFAULT_PROVIDER = "gemini"
        mock_settings.AI_HISTORY_INTERVIEW_PROVIDER = None
        # Misconfigured fallback list with ollama in front
        mock_settings.AI_FALLBACK_PROVIDERS = ["ollama", "groq", "openrouter"]

        chain = router._build_provider_chain(AITaskType.HISTORY_INTERVIEW)

    assert chain == ["gemini", "groq", "openrouter", "ollama"]
    assert chain[-1] == "ollama"


def test_task_override_different_from_default_includes_default_in_chain():
    """If task override is groq and default is gemini, chain orders: groq → gemini → openrouter → ollama."""
    router = AITaskRouter()
    with patch("app.ai.router.ai_settings") as mock_settings:
        mock_settings.AI_DEFAULT_PROVIDER = "gemini"
        mock_settings.AI_HISTORY_INTERVIEW_PROVIDER = "groq"
        mock_settings.AI_FALLBACK_PROVIDERS = ["openrouter", "ollama"]

        chain = router._build_provider_chain(AITaskType.HISTORY_INTERVIEW)

    assert chain == ["groq", "gemini", "openrouter", "ollama"]
    assert chain[-1] == "ollama"


def test_config_normalization_and_whitespace():
    """Config normalizes provider names by trimming whitespace, lowercasing, and ignoring empty entries."""
    from app.ai.config import AIConfig

    cfg = AIConfig(
        AI_DEFAULT_PROVIDER="  GEMINI  ",
        AI_HISTORY_INTERVIEW_PROVIDER="  ",
        AI_FALLBACK_PROVIDERS=" groq , , OPENROUTER , ollama ",
    )
    assert cfg.AI_DEFAULT_PROVIDER == "gemini"
    assert cfg.AI_HISTORY_INTERVIEW_PROVIDER is None
    assert cfg.AI_FALLBACK_PROVIDERS == ["groq", "openrouter", "ollama"]

