"""Document text extraction orchestrator.

Coordinates between digital PDF extraction and OCR image extraction,
handling multi-page documents, language configuration, and warnings.
"""

from __future__ import annotations

import logging
from pathlib import Path

from app.core.config import settings
from app.documents.ocr import (
    OCRError,
    OCRProvider,
    OCRResult,
    extract_embedded_pdf_text,
    get_ocr_provider,
)

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Orchestrates document text extraction across PDF and image formats."""

    def __init__(self, ocr_provider: OCRProvider | None = None) -> None:
        self.ocr_provider = ocr_provider or get_ocr_provider()

    async def extract_document_text(
        self,
        file_path: Path,
        mime_type: str,
        language: str | None = None,
    ) -> OCRResult:
        """Extract text from the specified document.

        For PDFs, first attempts lossless digital text extraction via pypdf.
        Falls back to OCR provider for scanned PDFs or images.
        """
        lang = language or settings.OCR_DEFAULT_LANGUAGE or "eng"

        # 1. Digital PDF extraction path
        if mime_type == "application/pdf":
            pdf_result = extract_embedded_pdf_text(file_path)
            if pdf_result is not None:
                logger.info(
                    "Extracted %d characters across %d pages via digital PDF reader.",
                    pdf_result.character_count,
                    pdf_result.page_count,
                )
                return pdf_result

        # 2. Image / Optical Character Recognition path
        logger.info(
            "Invoking OCR provider %s for mime_type=%s, lang=%s",
            self.ocr_provider.name,
            mime_type,
            lang,
        )
        result = await self.ocr_provider.extract_text(
            file_path=file_path,
            mime_type=mime_type,
            language=lang,
        )

        if not result.text.strip():
            result.warnings.append("No readable text could be identified in this document.")

        return result


# Singleton instance
document_processor = DocumentProcessor()
