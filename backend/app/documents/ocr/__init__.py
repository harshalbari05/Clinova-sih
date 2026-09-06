"""OCR Provider package factory."""

from __future__ import annotations

from app.core.config import settings
from app.documents.ocr.base import (
    OCRError,
    OCRPageResult,
    OCRProvider,
    OCRResult,
    extract_embedded_pdf_text,
)
from app.documents.ocr.tesseract import TesseractOCRProvider

_PROVIDERS: dict[str, type[OCRProvider]] = {
    "tesseract": TesseractOCRProvider,
}


def get_ocr_provider(provider_name: str | None = None) -> OCRProvider:
    """Instantiate the configured OCR provider."""
    name = (provider_name or settings.OCR_PROVIDER or "tesseract").lower().strip()
    provider_cls = _PROVIDERS.get(name, TesseractOCRProvider)
    return provider_cls()


__all__ = [
    "OCRError",
    "OCRPageResult",
    "OCRProvider",
    "OCRResult",
    "TesseractOCRProvider",
    "extract_embedded_pdf_text",
    "get_ocr_provider",
]
