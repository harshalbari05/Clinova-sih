from typing import Any

from fastapi import HTTPException, status


class ClinovaException(HTTPException):
    """Base exception for application-level errors."""

    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: Any = None,
        headers: dict[str, str] | None = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
