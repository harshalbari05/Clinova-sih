"""Base abstractions and data structures for OCR / text extraction.

Supports provider-independent OCR results, page-by-page tracking,
embedded PDF text extraction, and graceful failure reporting.
"""

from __future__ import annotations

import abc
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class OCRError(Exception):
    """Exception raised when OCR processing fails."""

    def __init__(self, message: str, provider: str = "unknown", category: str = "ocr_failure") -> None:
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.category = category


@dataclass
class OCRPageResult:
    """Extracted text and confidence for a single document page."""

    page_number: int
    text: str
    confidence: float | None = None


@dataclass
class OCRResult:
    """Consolidated result from OCR or digital document extraction."""

    text: str
    pages: list[OCRPageResult] = field(default_factory=list)
    provider: str = "unknown"
    language: str = "eng"
    confidence: float | None = None
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def character_count(self) -> int:
        return len(self.text)


class OCRProvider(abc.ABC):
    """Abstract interface for OCR and text extraction engines."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Name of the OCR provider."""
        pass

    @abc.abstractmethod
    async def extract_text(
        self,
        file_path: Path,
        mime_type: str,
        language: str = "eng",
    ) -> OCRResult:
        """Extract text from a document or image file."""
        pass

    @abc.abstractmethod
    def supported_mime_types(self) -> set[str]:
        """Return the set of MIME types supported by this provider."""
        pass


def extract_embedded_pdf_text(file_path: Path) -> OCRResult | None:
    """Extract embedded digital text from a PDF file using pypdf without OCR overhead.

    Returns OCRResult if readable embedded text is present, or None if the PDF
    is image-based / scanned and requires optical character recognition.
    """
    try:
        import pypdf

        reader = pypdf.PdfReader(str(file_path))
        pages: list[OCRPageResult] = []
        full_text_parts: list[str] = []

        for idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            clean_page_text = page_text.strip()
            pages.append(
                OCRPageResult(
                    page_number=idx + 1,
                    text=clean_page_text,
                    confidence=1.0 if clean_page_text else None,
                )
            )
            if clean_page_text:
                full_text_parts.append(f"--- Page {idx + 1} ---\n{clean_page_text}")

        total_extracted_text = "\n\n".join(full_text_parts).strip()

        # If substantial text exists (> 15 non-whitespace characters), treat as digital PDF
        if len(total_extracted_text) >= 15:
            return OCRResult(
                text=total_extracted_text,
                pages=pages,
                provider="pypdf_embedded",
                language="auto",
                confidence=1.0,
                warnings=[],
                metadata={
                    "page_count": len(reader.pages),
                    "character_count": len(total_extracted_text),
                    "digital_pdf": True,
                },
            )
        logger.info("PDF has insufficient embedded text; falling back to OCR.")
        return None
    except Exception as exc:
        logger.warning("Could not extract embedded PDF text: %s. Falling back to OCR.", exc)
        return None
