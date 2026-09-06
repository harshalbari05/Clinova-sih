"""AI providers sub-package.

Provider adapters live here. Each adapter imports only the SDK it
needs — SDK imports MUST NOT leak outside this sub-package.

Exported from here for convenience:
    AIProvider — the abstract base all adapters implement.
"""

from app.ai.providers.base import AIProvider

__all__ = ["AIProvider"]
