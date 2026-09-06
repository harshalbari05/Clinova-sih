"""Clinova AI provider package.

This package provides a provider-independent AI abstraction layer.
Application code should import from here rather than from any
provider-specific SDK.

Public surface:
    - AIProvider       — abstract provider interface
    - AIRequest        — provider-agnostic request schema
    - AIResponse       — provider-agnostic response schema
    - AIMessageInput   — single conversation turn
    - AIProviderError  — structured provider error
    - AIErrorKind      — error category enum
    - AITaskType       — clinical task enum
    - AITaskRouter     — task-to-provider mapping with fallback
    - get_provider     — provider factory
"""

from app.ai.providers.base import AIProvider
from app.ai.registry import get_provider
from app.ai.router import AITaskRouter
from app.ai.schemas import (
    AIErrorKind,
    AIMessageInput,
    AIProviderError,
    AIRequest,
    AIResponse,
)
from app.ai.tasks import AITaskType

__all__ = [
    "AIErrorKind",
    "AIMessageInput",
    "AIProvider",
    "AIProviderError",
    "AIRequest",
    "AIResponse",
    "AITaskRouter",
    "AITaskType",
    "get_provider",
]
