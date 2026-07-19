"""
extract_image.py — Image Text Extractor
=======================================
Extracts text from PNG, JPG, JPEG files using EasyOCR.
"""

from __future__ import annotations
import io
import logging

from extractors.ocr_processor import extract_text_from_image_bytes

logger = logging.getLogger(__name__)

def extract_image(file: io.IOBase) -> str:
    """
    Extract readable text from an image file.
    """
    try:
        raw_bytes = file.read()
        file.seek(0)
        return extract_text_from_image_bytes(raw_bytes)
    except Exception as exc:
        logger.exception("Image extraction failed.")
        raise RuntimeError(f"Image text extraction failed: {exc}") from exc
