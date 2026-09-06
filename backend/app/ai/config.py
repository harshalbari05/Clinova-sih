"""AI provider configuration for Clinova.

Extends the application settings pattern (pydantic-settings) with
all AI provider and task routing environment variables.

Usage:
    from app.ai.config import ai_settings

    provider_name = ai_settings.AI_DEFAULT_PROVIDER
    api_key       = ai_settings.GEMINI_API_KEY

Environment variables (all optional unless the relevant provider
is the active selection for a task):

  AI provider selection:
    AI_DEFAULT_PROVIDER           — fallback provider for all tasks (default: ollama)
    AI_HISTORY_INTERVIEW_PROVIDER — override for HISTORY_INTERVIEW task
    AI_STRUCTURED_EXTRACTION_PROVIDER
    AI_CLINICAL_SUMMARY_PROVIDER
    AI_DOCUMENT_ANALYSIS_PROVIDER
    AI_TRANSLATION_PROVIDER
    AI_TRIAGE_PROVIDER

  Fallbacks (comma-separated provider names):
    AI_FALLBACK_PROVIDERS         — global fallback chain, e.g. "ollama,openai"

  Gemini:
    GEMINI_API_KEY
    GEMINI_MODEL                  (default: gemini-2.0-flash)

  OpenAI (and compatible):
    OPENAI_API_KEY
    OPENAI_MODEL                  (default: gpt-4o-mini)
    OPENAI_BASE_URL               (optional; for Groq/OpenRouter/Cerebras)

  Groq (OpenAI-compatible):
    GROQ_API_KEY
    GROQ_MODEL                    (default: llama-3.3-70b-versatile)

  OpenRouter:
    OPENROUTER_API_KEY
    OPENROUTER_MODEL              (default: openai/gpt-4o-mini)

  Ollama (local):
    OLLAMA_BASE_URL               (default: http://localhost:11434)
    OLLAMA_MODEL                  (default: llama3.2)

Security:
    - API keys are read from environment only.
    - Keys are NEVER logged or returned in responses.
    - Missing optional keys do NOT crash app startup.
"""

from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AIConfig(BaseSettings):
    """AI provider and task routing configuration.

    All fields are optional at startup. A provider's credentials are
    only required when that provider is selected for an active task.
    """

    # ------------------------------------------------------------------
    # Provider selection
    # ------------------------------------------------------------------

    AI_DEFAULT_PROVIDER: str = "ollama"
    """Provider used for any task that doesn't have an explicit override."""

    # Per-task provider overrides (None = use AI_DEFAULT_PROVIDER)
    AI_HISTORY_INTERVIEW_PROVIDER: str | None = None
    AI_STRUCTURED_EXTRACTION_PROVIDER: str | None = None
    AI_CLINICAL_SUMMARY_PROVIDER: str | None = None
    AI_DOCUMENT_ANALYSIS_PROVIDER: str | None = None
    AI_TRANSLATION_PROVIDER: str | None = None
    AI_TRIAGE_PROVIDER: str | None = None

    # Global fallback chain (tried in order after primary fails)
    AI_FALLBACK_PROVIDERS: list[str] = []

    @field_validator("AI_FALLBACK_PROVIDERS", mode="before")
    @classmethod
    def parse_fallback_providers(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [p.strip() for p in v.split(",") if p.strip()]
        return v if isinstance(v, list) else []

    # ------------------------------------------------------------------
    # Gemini
    # ------------------------------------------------------------------

    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # ------------------------------------------------------------------
    # OpenAI (and compatible)
    # ------------------------------------------------------------------

    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: str | None = None
    """Override for OpenAI-compatible endpoints (Groq, OpenRouter, Cerebras)."""

    # ------------------------------------------------------------------
    # Groq (OpenAI-compatible shortcut)
    # ------------------------------------------------------------------

    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # ------------------------------------------------------------------
    # OpenRouter
    # ------------------------------------------------------------------

    OPENROUTER_API_KEY: str | None = None
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"

    # ------------------------------------------------------------------
    # Ollama (local)
    # ------------------------------------------------------------------

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# Singleton instance used throughout the application
ai_settings = AIConfig()
