"""AI provider registry / factory.

Responsible for constructing and returning AIProvider instances
by name. Providers are instantiated lazily on first request
(not at application startup).

Usage:
    from app.ai.registry import get_provider

    provider = get_provider("gemini")    # → GeminiProvider
    provider = get_provider("openai")    # → OpenAIProvider
    provider = get_provider("ollama")    # → OllamaProvider
    provider = get_provider("groq")      # → OpenAIProvider (Groq base_url)
    provider = get_provider("openrouter") # → OpenAIProvider (OpenRouter base_url)

Provider instances are cached after first creation so the SDK client
is shared across requests (lazy-init inside each adapter still applies).

Unknown provider names raise AIProviderError(AIErrorKind.AUTH_ERROR)
with a clear configuration message.

Security:
    - Provider credentials are read from ai_settings, not from callers.
    - API keys are never logged.
    - Providers whose credentials are missing raise AIProviderError
      only when generate() is called, not at startup.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.ai.config import ai_settings
from app.ai.schemas import AIErrorKind, AIProviderError

if TYPE_CHECKING:
    from app.ai.providers.base import AIProvider

logger = logging.getLogger(__name__)

# Cache of already-created provider instances
_provider_cache: dict[str, "AIProvider"] = {}

# Known provider names
_KNOWN_PROVIDERS: frozenset[str] = frozenset(
    {"gemini", "openai", "ollama", "groq", "openrouter"}
)

# OpenAI-compatible provider configs: name → (api_key_attr, model_attr, base_url)
_OPENAI_COMPATIBLE: dict[str, tuple[str, str, str]] = {
    "groq": (
        "GROQ_API_KEY",
        "GROQ_MODEL",
        "https://api.groq.com/openai/v1",
    ),
    "openrouter": (
        "OPENROUTER_API_KEY",
        "OPENROUTER_MODEL",
        "https://openrouter.ai/api/v1",
    ),
}


def get_provider(name: str) -> "AIProvider":
    """Return an AIProvider instance for the given provider name.

    Provider instances are cached — the factory is called only once
    per provider name per process lifetime.

    Args:
        name: Provider identifier, e.g. "gemini", "openai", "ollama",
              "groq", "openrouter".

    Returns:
        An AIProvider instance ready to call .generate() on.

    Raises:
        AIProviderError(AIErrorKind.AUTH_ERROR): If the provider name is
            unknown or not in the supported registry.
    """
    name = name.lower().strip()

    if name in _provider_cache:
        return _provider_cache[name]

    if name not in _KNOWN_PROVIDERS:
        raise AIProviderError(
            kind=AIErrorKind.AUTH_ERROR,
            provider=name,
            message=(
                f"Unknown AI provider: '{name}'. "
                f"Supported providers: {sorted(_KNOWN_PROVIDERS)}. "
                "To add a new provider, implement AIProvider and register it here."
            ),
        )

    provider = _create_provider(name)
    _provider_cache[name] = provider
    logger.debug("AI provider '%s' registered in registry.", name)
    return provider


def _create_provider(name: str) -> "AIProvider":
    """Instantiate a fresh provider adapter. Called once per provider name."""
    if name == "gemini":
        return _create_gemini()
    if name == "openai":
        return _create_openai()
    if name == "ollama":
        return _create_ollama()
    if name in _OPENAI_COMPATIBLE:
        return _create_openai_compatible(name)

    # Should not be reachable given _KNOWN_PROVIDERS guard above.
    raise AIProviderError(
        kind=AIErrorKind.AUTH_ERROR,
        provider=name,
        message=f"Provider '{name}' is registered but has no factory implementation.",
    )


def _create_gemini() -> "AIProvider":
    """Build GeminiProvider.

    API key is passed at construction but not used until generate() is called.
    Missing key does NOT fail here — the provider raises AUTH_ERROR on generate().
    """
    from app.ai.providers.gemini import GeminiProvider

    api_key = ai_settings.GEMINI_API_KEY or ""
    return GeminiProvider(api_key=api_key, model=ai_settings.GEMINI_MODEL)


def _create_openai() -> "AIProvider":
    """Build OpenAIProvider for api.openai.com."""
    from app.ai.providers.openai import OpenAIProvider

    api_key = ai_settings.OPENAI_API_KEY or ""
    return OpenAIProvider(
        api_key=api_key,
        model=ai_settings.OPENAI_MODEL,
        base_url=ai_settings.OPENAI_BASE_URL,
        provider_name="openai",
    )


def _create_openai_compatible(name: str) -> "AIProvider":
    """Build an OpenAIProvider for a compatible endpoint (Groq, OpenRouter)."""
    from app.ai.providers.openai import OpenAIProvider

    key_attr, model_attr, default_base_url = _OPENAI_COMPATIBLE[name]
    api_key = getattr(ai_settings, key_attr, None) or ""
    model = getattr(ai_settings, model_attr, "")
    return OpenAIProvider(
        api_key=api_key,
        model=model,
        base_url=default_base_url,
        provider_name=name,
    )


def _create_ollama() -> "AIProvider":
    """Build OllamaProvider for local inference."""
    from app.ai.providers.ollama import OllamaProvider

    return OllamaProvider(
        base_url=ai_settings.OLLAMA_BASE_URL,
        model=ai_settings.OLLAMA_MODEL,
    )


def clear_provider_cache() -> None:
    """Clear the provider instance cache.

    Intended for use in tests that need to re-instantiate providers
    with different settings.
    """
    _provider_cache.clear()
