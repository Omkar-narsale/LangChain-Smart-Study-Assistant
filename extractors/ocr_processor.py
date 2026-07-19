"""
ocr_processor.py — Centralized OCR Processing
=============================================
Initializes and caches the EasyOCR reader to avoid reloading the heavy model.
Provides a single function to extract text from images.
"""

from __future__ import annotations
import logging
import io

import streamlit as st
import easyocr
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

@st.cache_resource(show_spinner=False)
def _get_ocr_reader() -> easyocr.Reader:
    """Initialize and cache the EasyOCR reader."""
    logger.info("Initializing EasyOCR reader (this may take a moment)...")
    # Use English. Fallback to CPU if GPU isn't available
    return easyocr.Reader(['en'], gpu=False)

def extract_text_from_image_bytes(file_bytes: bytes) -> str:
    """
    Extract text from raw image bytes using EasyOCR.
    Handles handwritten notes and printed text.
    """
    try:
        reader = _get_ocr_reader()
        image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        # Convert PIL image to numpy array for EasyOCR
        img_np = np.array(image)
        
        # detail=0 returns a list of strings instead of bounding boxes
        results = reader.readtext(img_np, detail=0)
        
        if not results:
            logger.warning("OCR returned no text for this image.")
            return ""
            
        return "\n".join(results)
    except Exception as exc:
        logger.exception("OCR failed.")
        raise RuntimeError(f"OCR failed: {exc}") from exc
