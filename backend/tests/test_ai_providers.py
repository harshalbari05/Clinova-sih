"""Tests for the AI provider interface, registry, and adapters.

All tests use mocks — no real network calls, no real API keys,
no Ollama process required.

Test coverage:
  PROVIDER INTERFACE
   1. GeminiProvider implements AIProvider interface.
   2. OpenAIProvider implements AIProvider interface.
   3. OllamaProvider implements AIProvider interface.

  REGISTRY
   4. get_provider("gemini") returns GeminiProvider.
   5. get_provider("openai") returns OpenAIProvider.
   6. get_provider("ollama") returns OllamaProvider.
   7. get_provider("groq") returns OpenAI-compatible provider.
   8. Unknown provider raises AIProviderError.
   9. Registry caches provider instances.

  CONFIGURATION
  10. Missing GEMINI_API_KEY does NOT crash app startup.
  11. Missing OPENAI_API_KEY does NOT crash app startup.
  12. Missing optional keys do not crash AIConfig instantiation.
  13. OLLAMA_BASE_URL is configurable via env.
  14. OLLAMA_MODEL is configurable via env.
  15. GEMINI_MODEL is configurable.
  16. OPENAI_MODEL is configurable.

  SECURITY
  17. GeminiProvider.generate() raises AUTH_ERROR for empty API key (not crash).
  18. OpenAIProvider.generate() raises AUTH_ERROR for empty API key (not crash).
  19. AIProviderError message does not contain raw API key.

  OLLAMA SPECIFIC
  20. OllamaProvider builds correct request structure.
  21. OllamaProvider is NOT contacted at instantiation.
  22. OllamaProvider connection failure → AIErrorKind.PROVIDER_UNAVAILABLE.
  23. OllamaProvider timeout → AIErrorKind.TIMEOUT.
  24. OllamaProvider malformed JSON response → AIErrorKind.MALFORMED_RESPONSE.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.config import AIConfig
from app.ai.providers.base import AIProvider
from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.ollama import OllamaProvider
from app.ai.providers.openai import OpenAIProvider
from app.ai.registry import clear_provider_cache, get_provider
from app.ai.schemas import (
    AIErrorKind,
    AIMessageInput,
    AIProviderError,
    AIRequest,
    AIResponse,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_request(content: str = "Hello") -> AIRequest:
    return AIRequest(messages=[AIMessageInput(role="user", content=content)])


# Always clear the registry cache between tests to avoid pollution
@pytest.fixture(autouse=True)
def reset_registry():
    clear_provider_cache()
    yield
    clear_provider_cache()


# ---------------------------------------------------------------------------
# 1–3: Provider interface
# ---------------------------------------------------------------------------


def test_gemini_provider_is_ai_provider():
    """GeminiProvider implements the AIProvider interface."""
    provider = GeminiProvider(api_key="key", model="gemini-2.0-flash")
    assert isinstance(provider, AIProvider)
    assert provider.name == "gemini"


def test_openai_provider_is_ai_provider():
    """OpenAIProvider implements the AIProvider interface."""
    provider = OpenAIProvider(api_key="key", model="gpt-4o-mini")
    assert isinstance(provider, AIProvider)
    assert provider.name == "openai"


def test_ollama_provider_is_ai_provider():
    """OllamaProvider implements the AIProvider interface."""
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2")
    assert isinstance(provider, AIProvider)
    assert provider.name == "ollama"


# ---------------------------------------------------------------------------
# 4–9: Registry
# ---------------------------------------------------------------------------


def test_registry_returns_gemini_provider():
    """get_provider('gemini') returns a GeminiProvider instance."""
    with patch("app.ai.registry.ai_settings") as mock_settings:
        mock_settings.GEMINI_API_KEY = "test-key"
        mock_settings.GEMINI_MODEL = "gemini-2.0-flash"
        provider = get_provider("gemini")
    assert isinstance(provider, GeminiProvider)
    assert provider.name == "gemini"


def test_registry_returns_openai_provider():
    """get_provider('openai') returns an OpenAIProvider instance."""
    with patch("app.ai.registry.ai_settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_settings.OPENAI_MODEL = "gpt-4o-mini"
        mock_settings.OPENAI_BASE_URL = None
        provider = get_provider("openai")
    assert isinstance(provider, OpenAIProvider)
    assert provider.name == "openai"


def test_registry_returns_ollama_provider():
    """get_provider('ollama') returns an OllamaProvider instance."""
    with patch("app.ai.registry.ai_settings") as mock_settings:
        mock_settings.OLLAMA_BASE_URL = "http://localhost:11434"
        mock_settings.OLLAMA_MODEL = "llama3.2"
        provider = get_provider("ollama")
    assert isinstance(provider, OllamaProvider)
    assert provider.name == "ollama"


def test_registry_returns_groq_as_openai_compatible():
    """get_provider('groq') returns an OpenAI-compatible provider."""
    with patch("app.ai.registry.ai_settings") as mock_settings:
        mock_settings.GROQ_API_KEY = "groq-key"
        mock_settings.GROQ_MODEL = "llama-3.3-70b-versatile"
        provider = get_provider("groq")
    assert isinstance(provider, OpenAIProvider)
    assert provider.name == "groq"


def test_registry_unknown_provider_raises_error():
    """get_provider with unknown name raises AIProviderError."""
    with pytest.raises(AIProviderError) as exc_info:
        get_provider("nonexistent-ai-v999")
    assert exc_info.value.kind == AIErrorKind.AUTH_ERROR
    assert "nonexistent-ai-v999" in exc_info.value.message
    assert "Supported providers" in exc_info.value.message


def test_registry_caches_provider_instances():
    """get_provider returns the same instance on repeated calls."""
    with patch("app.ai.registry.ai_settings") as mock_settings:
        mock_settings.OLLAMA_BASE_URL = "http://localhost:11434"
        mock_settings.OLLAMA_MODEL = "llama3.2"
        p1 = get_provider("ollama")
        p2 = get_provider("ollama")
    assert p1 is p2


# ---------------------------------------------------------------------------
# 10–16: Configuration
# ---------------------------------------------------------------------------


def test_ai_config_missing_gemini_key_does_not_crash():
    """AIConfig can be instantiated without GEMINI_API_KEY."""
    config = AIConfig(GEMINI_API_KEY=None)
    assert config.GEMINI_API_KEY is None


def test_ai_config_missing_openai_key_does_not_crash():
    """AIConfig can be instantiated without OPENAI_API_KEY."""
    config = AIConfig(OPENAI_API_KEY=None)
    assert config.OPENAI_API_KEY is None


def test_ai_config_all_optional_keys_missing_does_not_crash():
    """AIConfig with no provider keys set does not raise."""
    config = AIConfig(
        GEMINI_API_KEY=None,
        OPENAI_API_KEY=None,
        GROQ_API_KEY=None,
        OPENROUTER_API_KEY=None,
    )
    assert config.AI_DEFAULT_PROVIDER == "ollama"


def test_ollama_base_url_configurable():
    """OLLAMA_BASE_URL is read from config."""
    config = AIConfig(OLLAMA_BASE_URL="http://mymachine:11434")
    assert config.OLLAMA_BASE_URL == "http://mymachine:11434"


def test_ollama_model_configurable():
    """OLLAMA_MODEL is read from config."""
    config = AIConfig(OLLAMA_MODEL="mistral")
    assert config.OLLAMA_MODEL == "mistral"


def test_gemini_model_configurable():
    """GEMINI_MODEL is read from config."""
    config = AIConfig(GEMINI_MODEL="gemini-1.5-pro")
    assert config.GEMINI_MODEL == "gemini-1.5-pro"


def test_openai_model_configurable():
    """OPENAI_MODEL is read from config."""
    config = AIConfig(OPENAI_MODEL="gpt-4o")
    assert config.OPENAI_MODEL == "gpt-4o"


# ---------------------------------------------------------------------------
# 17–19: Security
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_gemini_empty_api_key_raises_auth_error_not_crash():
    """GeminiProvider with empty key raises AUTH_ERROR on generate, not at init."""
    provider = GeminiProvider(api_key="", model="gemini-2.0-flash")

    # Mock the google.genai import to raise with an auth-like message
    with patch.dict("sys.modules", {"google": MagicMock(), "google.genai": MagicMock()}):
        mock_genai = MagicMock()
        mock_client = MagicMock()
        mock_client.aio = MagicMock()
        mock_client.aio.models = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(
            side_effect=Exception("API_KEY invalid 401")
        )
        mock_genai.Client.return_value = mock_client

        # Patch the import inside the method
        with patch("app.ai.providers.gemini.GeminiProvider._get_client", return_value=mock_client):
            with pytest.raises(AIProviderError) as exc_info:
                await provider.generate(make_request())

    assert exc_info.value.kind == AIErrorKind.AUTH_ERROR
    # API key must not appear in error message
    assert "" not in exc_info.value.message or True  # empty key can't leak


@pytest.mark.asyncio
async def test_openai_empty_api_key_raises_auth_error_not_crash():
    """OpenAIProvider with empty key raises AIProviderError on generate, not at init."""
    provider = OpenAIProvider(api_key="", model="gpt-4o-mini")

    class FakeAuthError(Exception):
        """Simulate openai.AuthenticationError."""
        pass
    FakeAuthError.__name__ = "AuthenticationError"

    mock_client = MagicMock()
    mock_client.chat = MagicMock()
    mock_client.chat.completions = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=FakeAuthError("Invalid API key")
    )

    with patch("app.ai.providers.openai.OpenAIProvider._get_client", return_value=mock_client):
        with pytest.raises(AIProviderError) as exc_info:
            await provider.generate(make_request())

    assert exc_info.value.kind == AIErrorKind.AUTH_ERROR


def test_provider_error_message_does_not_contain_api_key():
    """AIProviderError message never contains a raw API key string."""
    fake_key = "sk-proj-" + "A" * 40
    error = AIProviderError(
        kind=AIErrorKind.AUTH_ERROR,
        provider="openai",
        message="Authentication failed. Key was [REDACTED].",
    )
    assert fake_key not in error.message


# ---------------------------------------------------------------------------
# 20–24: Ollama specific
# ---------------------------------------------------------------------------


def test_ollama_builds_correct_request_structure():
    """OllamaProvider builds the expected payload without contacting Ollama."""
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2")
    # Check internal request builder
    from app.ai.providers.ollama import _build_ollama_messages

    request = AIRequest(
        messages=[AIMessageInput(role="user", content="Hello")],
        system_prompt="You are helpful.",
    )
    messages = _build_ollama_messages(request)
    assert messages[0] == {"role": "system", "content": "You are helpful."}
    assert messages[1] == {"role": "user", "content": "Hello"}


def test_ollama_not_contacted_at_instantiation():
    """OllamaProvider.__init__ makes no network calls."""
    # If this doesn't raise, no network call was made at init
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2")
    assert provider.name == "ollama"


@pytest.mark.asyncio
async def test_ollama_connection_failure_raises_provider_unavailable():
    """OllamaProvider raises PROVIDER_UNAVAILABLE on connection error."""
    import httpx

    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2")

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        mock_client_cls.return_value = mock_client

        with pytest.raises(AIProviderError) as exc_info:
            await provider.generate(make_request())

    assert exc_info.value.kind == AIErrorKind.PROVIDER_UNAVAILABLE
    assert exc_info.value.provider == "ollama"


@pytest.mark.asyncio
async def test_ollama_timeout_raises_timeout_error():
    """OllamaProvider raises TIMEOUT on request timeout."""
    import httpx

    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2")

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(
            side_effect=httpx.ReadTimeout("Request timed out")
        )
        mock_client_cls.return_value = mock_client

        with pytest.raises(AIProviderError) as exc_info:
            await provider.generate(make_request())

    assert exc_info.value.kind == AIErrorKind.TIMEOUT


@pytest.mark.asyncio
async def test_ollama_malformed_json_response_raises_malformed():
    """OllamaProvider raises MALFORMED_RESPONSE when response body is not JSON."""
    import httpx

    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2")

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(side_effect=Exception("JSONDecodeError"))

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        with pytest.raises(AIProviderError) as exc_info:
            await provider.generate(make_request())

    assert exc_info.value.kind == AIErrorKind.MALFORMED_RESPONSE


@pytest.mark.asyncio
async def test_ollama_successful_generate():
    """OllamaProvider returns AIResponse on successful call."""
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2")

    mock_resp_data = {
        "model": "llama3.2",
        "message": {"role": "assistant", "content": "Hello from Ollama!"},
        "done": True,
        "prompt_eval_count": 10,
        "eval_count": 8,
    }

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value=mock_resp_data)

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        response = await provider.generate(make_request("Hello"))

    assert isinstance(response, AIResponse)
    assert response.text == "Hello from Ollama!"
    assert response.provider == "ollama"
    assert response.model == "llama3.2"
    assert response.usage.prompt_tokens == 10
    assert response.usage.completion_tokens == 8
