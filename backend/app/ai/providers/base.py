"""Abstract AIProvider base class.

All provider adapters (Gemini, OpenAI, Ollama, …) must subclass
AIProvider and implement the generate() coroutine.

Application code and services should depend ONLY on AIProvider —
never on concrete adapter classes or provider SDK types.
"""

from __future__ import annotations

import abc

from app.ai.schemas import AIRequest, AIResponse


class AIProvider(abc.ABC):
    """Abstract base class for all AI provider adapters.

    Contract:
        - generate() is the single normalised entry point.
        - Providers convert AIRequest to provider-specific calls internally.
        - Providers convert provider-specific responses to AIResponse.
        - Providers raise AIProviderError (from app.ai.schemas) on failure.
        - Provider SDK imports MUST stay inside the adapter module.
        - Providers MUST NOT log API keys or patient conversation content.
        - Providers MUST NOT make network calls at instantiation time.
          (Lazy initialisation only — connect on first generate() call.)
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Short identifier for this provider, e.g. 'gemini', 'openai', 'ollama'."""
        ...

    @abc.abstractmethod
    async def generate(self, request: AIRequest) -> AIResponse:
        """Execute an AI inference request and return a normalised response.

        Args:
            request: Provider-agnostic AIRequest. Fields not supported by
                     this provider are silently ignored.

        Returns:
            AIResponse with at minimum .text and .provider populated.

        Raises:
            AIProviderError: On any failure. The error.kind field
                             categorises the failure for retry/fallback logic.
        """
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
