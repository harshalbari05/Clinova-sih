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

Fallback behaviour:
    - Maximum MAX_ATTEMPTS (3) total provider attempts.
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

MAX_ATTEMPTS = 3
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
                return override.lower().strip()
        return ai_settings.AI_DEFAULT_PROVIDER.lower().strip()

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

        Order: [primary] + AI_FALLBACK_PROVIDERS (deduplicated, capped at MAX_ATTEMPTS).
        """
        primary = self.get_provider_name_for_task(task)
        fallbacks = [p for p in ai_settings.AI_FALLBACK_PROVIDERS if p != primary]
        chain = [primary, *fallbacks]
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
