"""Storage provider abstraction for medical documents.

Decouples storage of raw binary documents from database metadata.
Supports local filesystem storage with path traversal protection,
safe unique identifier generation, and safe retrieval.
"""

from __future__ import annotations

import abc
import os
import re
import uuid
from pathlib import Path

from app.core.config import settings


class StorageError(Exception):
    """Base exception for document storage failures."""

    pass


class PathTraversalError(StorageError):
    """Raised when an unsafe path traversal attempt is detected."""

    pass


class StorageProvider(abc.ABC):
    """Abstract interface for storing and retrieving medical document binaries."""

    @abc.abstractmethod
    async def save_file(
        self,
        content: bytes,
        original_filename: str,
        patient_id: uuid.UUID,
    ) -> tuple[str, str]:
        """Save file content and return (storage_identifier, original_filename)."""
        pass

    @abc.abstractmethod
    def get_file_path(self, storage_identifier: str) -> Path:
        """Resolve a storage identifier to a local filesystem Path for streaming."""
        pass

    @abc.abstractmethod
    def file_exists(self, storage_identifier: str) -> bool:
        """Check if the document exists in storage."""
        pass

    @abc.abstractmethod
    async def delete_file(self, storage_identifier: str) -> bool:
        """Remove the document from storage if present."""
        pass


class LocalStorageProvider(StorageProvider):
    """Local filesystem storage implementation with path traversal safeguards."""

    def __init__(self, base_path: str | Path | None = None) -> None:
        raw_path = base_path or settings.MEDICAL_DOCUMENT_STORAGE_PATH
        self.base_dir = Path(raw_path).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_extension(self, filename: str) -> str:
        """Extract and sanitize file extension safely."""
        _, ext = os.path.splitext(filename)
        clean_ext = re.sub(r"[^a-zA-Z0-9_.]", "", ext.lower())
        if clean_ext and not clean_ext.startswith("."):
            clean_ext = f".{clean_ext}"
        return clean_ext

    def _verify_safe_path(self, target_path: Path) -> Path:
        """Verify that resolved target_path stays strictly within self.base_dir."""
        resolved = target_path.resolve()
        try:
            resolved.relative_to(self.base_dir)
        except ValueError as exc:
            raise PathTraversalError(
                f"Path traversal detected: {target_path} is outside {self.base_dir}"
            ) from exc
        return resolved

    async def save_file(
        self,
        content: bytes,
        original_filename: str,
        patient_id: uuid.UUID,
    ) -> tuple[str, str]:
        """Save raw bytes to a safe patient-namespaced unique file on disk."""
        ext = self._sanitize_extension(original_filename)
        # Unique safe filename: <patient_id>/<doc_uuid><ext>
        safe_key = f"{uuid.uuid4()}{ext}"
        patient_dir = self.base_dir / str(patient_id)
        patient_dir.mkdir(parents=True, exist_ok=True)

        target_path = self._verify_safe_path(patient_dir / safe_key)

        # Write binary content
        with open(target_path, "wb") as f:
            f.write(content)

        # Storage identifier is relative path: <patient_id>/<safe_key>
        storage_identifier = f"{patient_id}/{safe_key}"
        return storage_identifier, original_filename

    def get_file_path(self, storage_identifier: str) -> Path:
        """Resolve storage identifier to verified absolute Path."""
        if ".." in storage_identifier or "\0" in storage_identifier:
            raise PathTraversalError("Invalid storage identifier characters.")

        target = self.base_dir / storage_identifier
        verified = self._verify_safe_path(target)
        if not verified.is_file():
            raise FileNotFoundError(f"Stored file not found: {storage_identifier}")
        return verified

    def file_exists(self, storage_identifier: str) -> bool:
        """Check whether the stored file exists."""
        try:
            target = self.base_dir / storage_identifier
            verified = self._verify_safe_path(target)
            return verified.is_file()
        except (PathTraversalError, ValueError):
            return False

    async def delete_file(self, storage_identifier: str) -> bool:
        """Delete stored file safely if it exists."""
        try:
            target = self.base_dir / storage_identifier
            verified = self._verify_safe_path(target)
            if verified.is_file():
                verified.unlink()
                return True
        except (PathTraversalError, ValueError, OSError):
            pass
        return False


# Singleton default storage provider
storage_provider: StorageProvider = LocalStorageProvider()
