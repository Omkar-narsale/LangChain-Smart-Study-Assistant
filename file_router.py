"""
file_router.py — Modular Document Extractor Router
==================================================
Routes uploaded files to the correct extraction module based on MIME type or extension.
"""

from __future__ import annotations

import io
import logging
import streamlit as st

from extractors.extract_pdf import extract_pdf
from extractors.extract_ppt import extract_ppt
from extractors.extract_docx import extract_docx
from extractors.extract_image import extract_image

logger = logging.getLogger(__name__)

# Supported MIME types mapping to internal identifiers
_SUPPORTED_TYPES: dict[str, str] = {
    "text/plain": "txt",
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.ms-powerpoint": "ppt",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
    "image/png": "image",
    "image/jpeg": "image",
    "image/jpg": "image",
}

def _load_txt(file: io.IOBase) -> str:
    """Extract plain text from a UTF-8 encoded text file."""
    raw_bytes = file.read()
    return raw_bytes.decode("utf-8", errors="replace")

def load_document(uploaded_file) -> str:
    """
    Route the uploaded file to the appropriate extraction module.
    """
    mime_type: str = getattr(uploaded_file, 'type', None)
    
    # Fallback to extension if MIME type is generic
    if not mime_type or mime_type == "application/octet-stream":
        ext = uploaded_file.name.split('.')[-1].lower()
        ext_to_mime = {
            "txt": "text/plain",
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "ppt": "application/vnd.ms-powerpoint",
            "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg"
        }
        mime_type = ext_to_mime.get(ext, "")
        
    format_tag = _SUPPORTED_TYPES.get(mime_type)

    if not format_tag:
        raise ValueError(
            f"Unsupported file type: '{mime_type}'. "
            f"Supported formats: PDF, PPT, PPTX, DOCX, TXT, PNG, JPG, JPEG"
        )

    logger.info("Routing document — format tag: %s", format_tag)
    
    # Initialize slide count to None (only updated for PPT)
    st.session_state["slide_count"] = None
    # Initialize OCR status to Not Used
    if "ocr_status" not in st.session_state or st.session_state["ocr_status"] != "Used":
        st.session_state["ocr_status"] = "Not Used"

    try:
        if format_tag == "txt":
            text = _load_txt(uploaded_file)
        elif format_tag == "pdf":
            text = extract_pdf(uploaded_file)
        elif format_tag == "docx":
            text = extract_docx(uploaded_file)
        elif format_tag in ["ppt", "pptx"]:
            text, slides = extract_ppt(uploaded_file)
            st.session_state["slide_count"] = slides
        elif format_tag == "image":
            text = extract_image(uploaded_file)
            st.session_state["ocr_status"] = "Used"
        else:
            raise ValueError(f"Unhandled format tag: {format_tag}")

    except Exception as exc:
        logger.exception("Failed to extract text from document.")
        raise RuntimeError(f"Text extraction failed: {exc}") from exc

    if "page_texts" not in st.session_state or not st.session_state["page_texts"]:
        st.session_state["page_texts"] = [text]

    extracted_length = len(text.strip())
    logger.info("Document loaded — %d characters extracted.", extracted_length)

    if extracted_length == 0:
        logger.warning("Extracted text is empty. The document may have no readable content.")
        st.warning("Extracted text is empty. The document may have no readable content.")

    return text
