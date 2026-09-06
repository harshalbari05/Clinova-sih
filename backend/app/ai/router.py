"""AI Task Router for Clinova.

Maps clinical task types → provider → model with fallback support.

Architecture:
    AITaskRouter
          ↓
    resolve task → provider name (from config)
          ↓
    get_provider(name) → AIProvider
          ↓
    provider.generate(AIRequest) → AIResponse

    On failure:
          ↓
    try next fallback provider
          ↓
    ... (up to MAX_ATTEMPTS total)
          ↓
    raise AIProviderError (last error)

Fallbacks and provider priority:
    - Normal production default is Gemini (or configured cloud provider).
    - Provider chain order:
        1. Task-specific provider override (if configured)
        2. Configured AI_DEFAULT_PROVIDER (if task override was active and differs)
        3. Configured AI_FALLBACK_PROVIDERS (Groq, OpenRouter)
        4. Ollama (strictly the last-resort local fallback)
    - Maximum MAX_ATTEMPTS (5) total provider attempts.
    - Non-retryable errors (AUTH_ERROR, INVALID_REQUEST) abort immediately
      without trying fallbacks.
    - Retryable errors (PROVIDER_UNAVAILABLE, RATE_LIMIT, TIMEOUT,
      MALFORMED_RESPONSE, UNEXPECTED_ERROR) trigger the next fallback.
    - If all providers fail, the last AIProviderError is re-raised.
    - Errors are always surfaced — never silently swallowed.

Configuration:
    Task → provider mapping is driven by ai_settings:
        AI_HISTORY_INTERVIEW_PROVIDER → overrides AI_DEFAULT_PROVIDER
        AI_FALLBACK_PROVIDERS          → global fallback chain

Usage:
    from app.ai.router import task_router
    from app.ai.tasks import AITaskType

    response = await task_router.generate(
        task=AITaskType.HISTORY_INTERVIEW,
        request=AIRequest(messages=[...], system_prompt="..."),
    )
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.ai.config import ai_settings
from app.ai.registry import get_provider
from app.ai.schemas import AIErrorKind, AIProviderError
from app.ai.tasks import AITaskType

if TYPE_CHECKING:
    from app.ai.providers.base import AIProvider
    from app.ai.schemas import AIRequest, AIResponse

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 5
"""Maximum total provider attempts (primary + fallbacks)."""

# Maps AITaskType → the ai_settings attribute that overrides the default provider
_TASK_PROVIDER_ATTR: dict[AITaskType, str] = {
    AITaskType.HISTORY_INTERVIEW: "AI_HISTORY_INTERVIEW_PROVIDER",
    AITaskType.STRUCTURED_EXTRACTION: "AI_STRUCTURED_EXTRACTION_PROVIDER",
    AITaskType.CLINICAL_SUMMARY: "AI_CLINICAL_SUMMARY_PROVIDER",
    AITaskType.DOCUMENT_ANALYSIS: "AI_DOCUMENT_ANALYSIS_PROVIDER",
    AITaskType.TRANSLATION: "AI_TRANSLATION_PROVIDER",
    AITaskType.TRIAGE: "AI_TRIAGE_PROVIDER",
}


class AITaskRouter:
    """Routes clinical AI tasks to the configured provider with fallback support.

    Instantiate once and reuse (e.g. as a module-level singleton).
    """

    def get_provider_name_for_task(self, task: AITaskType) -> str:
        """Return the configured primary provider name for a task.

        Looks up the task-specific override first, then falls back to
        AI_DEFAULT_PROVIDER.

        Args:
            task: The clinical task type.

        Returns:
            Provider name string, e.g. "gemini", "ollama", "openai".
        """
        attr = _TASK_PROVIDER_ATTR.get(task)
        if attr:
            override = getattr(ai_settings, attr, None)
            if override:
                override_clean = str(override).lower().strip()
                if override_clean:
                    return override_clean
        default_val = getattr(ai_settings, "AI_DEFAULT_PROVIDER", "gemini")
        return (default_val or "gemini").lower().strip()

    def get_provider_for_task(self, task: AITaskType) -> "AIProvider":
        """Return the AIProvider instance for the given task.

        Resolves the provider name from config and delegates to the registry.

        Args:
            task: The clinical task type.

        Returns:
            Configured AIProvider ready to call .generate() on.

        Raises:
            AIProviderError: If the provider name is unknown.
        """
        provider_name = self.get_provider_name_for_task(task)
        return get_provider(provider_name)

    def _build_provider_chain(self, task: AITaskType) -> list[str]:
        """Build the ordered list of provider names to try.

        Order:
        1. Task-specific provider (or AI_DEFAULT_PROVIDER if no override).
        2. Configured AI_DEFAULT_PROVIDER (if task override was active and differs).
        3. Configured AI_FALLBACK_PROVIDERS in order.
        4. Ollama is always placed LAST in the fallback chain unless explicitly
           selected as the primary provider.
        """
        primary = self.get_provider_name_for_task(task)
        default = (
            getattr(ai_settings, "AI_DEFAULT_PROVIDER", "gemini") or "gemini"
        ).lower().strip()

        chain: list[str] = [primary]

        # If a task override was active and differs from default provider,
        # try default provider next before other fallbacks
        if default and default != primary and default not in chain:
            chain.append(default)

        # Normalise and append configured fallback providers
        fallbacks = getattr(ai_settings, "AI_FALLBACK_PROVIDERS", []) or []
        for p in fallbacks:
            p_clean = str(p).lower().strip()
            if p_clean and p_clean not in chain:
                chain.append(p_clean)

        # Ensure Ollama is NEVER attempted before configured cloud providers,
        # unless developer explicitly selected Ollama as primary.
        if primary != "ollama" and "ollama" in chain:
            chain.remove("ollama")
            chain.append("ollama")

        return chain[:MAX_ATTEMPTS]

    async def generate(
        self,
        task: AITaskType,
        request: "AIRequest",
    ) -> "AIResponse":
        """Execute an AI request for the given task with fallback support.

        Tries the primary provider first. On retryable failures, tries
        each fallback provider in order. Aborts immediately on non-retryable
        errors (auth / invalid request).

        Args:
            task:    The clinical task type (determines provider selection).
            request: Provider-agnostic AI request.

        Returns:
            AIResponse from the first provider that succeeds.

        Raises:
            AIProviderError: If all providers fail. The error reflects
                             the last failure encountered.
        """
        provider_chain = self._build_provider_chain(task)
        last_error: AIProviderError | None = None

        for attempt, provider_name in enumerate(provider_chain, start=1):
            logger.debug(
                "AI task '%s': attempt %d/%d via provider '%s'.",
                task.value,
                attempt,
                len(provider_chain),
                provider_name,
            )
            try:
                provider = get_provider(provider_name)
                response = await provider.generate(request)
                if attempt > 1:
                    logger.info(
                        "AI task '%s': succeeded on attempt %d via '%s' "
                        "(primary '%s' failed).",
                        task.value,
                        attempt,
                        provider_name,
                        provider_chain[0],
                    )
                return response

            except AIProviderError as exc:
                last_error = exc

                if not exc.retryable:
                    # Non-retryable: abort immediately (misconfiguration / bad req)
                    logger.error(
                        "AI task '%s': non-retryable error from '%s': %s [%s]",
                        task.value,
                        provider_name,
                        exc.message,
                        exc.kind.value,
                    )
                    raise

                logger.warning(
                    "AI task '%s': retryable error from '%s': %s [%s]. "
                    "Trying next provider.",
                    task.value,
                    provider_name,
                    exc.message,
                    exc.kind.value,
                )

        # All providers exhausted
        if last_error is not None:
            logger.error(
                "AI task '%s': all %d provider(s) failed. Last error: %s",
                task.value,
                len(provider_chain),
                last_error.message,
            )
            raise last_error

        # Defensive: unreachable if provider_chain is non-empty
        raise AIProviderError(
            kind=AIErrorKind.UNEXPECTED_ERROR,
            provider="router",
            message=f"No providers configured for task '{task.value}'.",
        )


# Module-level singleton used by services
task_router = AITaskRouter()
