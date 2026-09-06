"""Tesseract OCR Provider with image preprocessing and graceful fallback.

Handles:
- Orientation and resolution normalization via Pillow.
- Multi-language configuration (English, Hindi, Marathi).
- Graceful error reporting when Tesseract binary is absent from host.
- Never mutates the original file on disk.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from app.documents.ocr.base import OCRError, OCRPageResult, OCRProvider, OCRResult

logger = logging.getLogger(__name__)

# Supported language code mapping
_LANG_MAP = {
    "eng": "eng",
    "english": "eng",
    "hin": "hin",
    "hindi": "hin",
    "mar": "mar",
    "marathi": "mar",
}


class TesseractOCRProvider(OCRProvider):
    """OCR provider implementing local Tesseract OCR with image preprocessing."""

    @property
    def name(self) -> str:
        return "tesseract"

    def supported_mime_types(self) -> set[str]:
        return {"image/jpeg", "image/png", "image/webp", "application/pdf"}

    def _preprocess_image(self, file_path: Path) -> Any:
        """Load and preprocess image using Pillow without altering disk file."""
        from PIL import Image, ImageOps

        image = Image.open(file_path)

        # 1. Correct EXIF orientation if present
        try:
            image = ImageOps.exif_transpose(image)
        except Exception:
            pass

        # 2. Convert to Grayscale for improved text contrast
        if image.mode != "L":
            image = image.convert("L")

        # 3. Downscale massive images (> 3000px) to prevent OCR memory stalls
        max_dim = 3000
        if image.width > max_dim or image.height > max_dim:
            image.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

        return image

    def _resolve_language_code(self, language: str) -> str:
        """Resolve requested language string to Tesseract language code."""
        clean = language.strip().lower()
        return _LANG_MAP.get(clean, "eng")

    async def extract_text(
        self,
        file_path: Path,
        mime_type: str,
        language: str = "eng",
    ) -> OCRResult:
        """Extract text from an image or document using Tesseract."""
        start_time = time.monotonic()
        tess_lang = self._resolve_language_code(language)
        warnings: list[str] = []

        try:
            import pytesseract
        except ImportError as exc:
            raise OCRError(
                "pytesseract library is not installed in the environment.",
                provider="tesseract",
                category="dependency_missing",
            ) from exc

        # Handle Images
        if mime_type.startswith("image/"):
            try:
                img = self._preprocess_image(file_path)
            except Exception as exc:
                raise OCRError(
                    f"Failed to load or preprocess image: {exc}",
                    provider="tesseract",
                    category="invalid_image",
                ) from exc

            try:
                # Extract text using pytesseract
                raw_text: Any = pytesseract.image_to_string(
                    img,
                    lang=tess_lang,
                    output_type=pytesseract.Output.STRING,
                )
                if isinstance(raw_text, dict):
                    extracted_text = str(raw_text.get("text", ""))
                elif isinstance(raw_text, bytes):
                    extracted_text = raw_text.decode("utf-8", errors="replace")
                else:
                    extracted_text = str(raw_text or "")

                # Attempt to retrieve mean confidence score
                confidence: float | None = None
                try:
                    data = pytesseract.image_to_data(
                        img,
                        lang=tess_lang,
                        output_type=pytesseract.Output.DICT,
                    )
                    confs = [
                        float(c)
                        for c in data.get("conf", [])
                        if str(c).replace(".", "", 1).isdigit() and float(c) >= 0
                    ]
                    if confs:
                        confidence = round(sum(confs) / len(confs) / 100.0, 3)
                except Exception as conf_err:
                    logger.debug("Could not compute Tesseract confidence: %s", conf_err)

                clean_text = extracted_text.strip()
                if not clean_text:
                    warnings.append("OCR produced empty or whitespace-only text.")

                elapsed = round(time.monotonic() - start_time, 3)
                return OCRResult(
                    text=clean_text,
                    pages=[
                        OCRPageResult(
                            page_number=1,
                            text=clean_text,
                            confidence=confidence,
                        )
                    ],
                    provider="tesseract",
                    language=tess_lang,
                    confidence=confidence,
                    warnings=warnings,
                    metadata={
                        "processing_seconds": elapsed,
                        "character_count": len(clean_text),
                        "page_count": 1,
                    },
                )
            except pytesseract.TesseractNotFoundError as exc:
                raise OCRError(
                    "Tesseract OCR executable is not installed or not in PATH.",
                    provider="tesseract",
                    category="tesseract_not_installed",
                ) from exc
            except Exception as exc:
                raise OCRError(
                    f"Tesseract OCR processing failed: {exc}",
                    provider="tesseract",
                    category="ocr_engine_error",
                ) from exc

        # Handle PDF (if digital text extraction was already bypassed or returned empty)
        raise OCRError(
            "Scanned PDF OCR requires image rasterization. Please upload digital PDF or high-resolution images.",
            provider="tesseract",
            category="unsupported_pdf_ocr",
        )
