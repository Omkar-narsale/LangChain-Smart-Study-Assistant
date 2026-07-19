"""
document_loader.py — Reusable Document Loader
===============================================
Provides a single public function:

    load_document(uploaded_file) -> str

Supported formats:
    • TXT  (.txt)
    • PDF  (.pdf)   — via PyPDF2
    • DOCX (.docx)  — via python-docx

Design notes:
    - This module is completely decoupled from Streamlit.
      It accepts any file-like object, making it testable and
      reusable in CLI scripts, API endpoints, or a future RAG pipeline.
    - Raises a ValueError for unsupported MIME types so the caller
      can surface a meaningful error to the user.

Future RAG extension:
    When adding chunking + embeddings, import this function and pipe
    its output into a text splitter — no changes needed here.
"""

from __future__ import annotations

import io
import logging
from typing import Union

import docx
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Supported MIME types → handler mapping
# ---------------------------------------------------------------------------

_SUPPORTED_TYPES: dict[str, str] = {
    "text/plain": "txt",
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}


# ---------------------------------------------------------------------------
# Internal handlers
# ---------------------------------------------------------------------------

def _load_txt(file: io.IOBase) -> str:
    """Extract plain text from a UTF-8 encoded text file."""
    raw_bytes = file.read()
    return raw_bytes.decode("utf-8", errors="replace")


def _load_pdf(file: io.IOBase) -> str:
    """
    Extract text from every page of a PDF.
    Pages that return None from extract_text() are silently skipped.
    """
    reader = PdfReader(file)
    pages: list[str] = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages.append(text.strip())
        else:
            logger.debug("PDF page %d returned no extractable text — skipping.", i)

    return "\n\n".join(pages)


def _load_docx(file: io.IOBase) -> str:
    """
    Extract paragraph text from a DOCX document.
    Empty paragraphs (section breaks, blank lines) are filtered out.
    """
    document = docx.Document(file)
    paragraphs: list[str] = [
        para.text.strip()
        for para in document.paragraphs
        if para.text.strip()
    ]
    return "\n\n".join(paragraphs)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_document(uploaded_file) -> str:
    """
    Load and extract plain text from an uploaded file.

    Accepts any file-like object that exposes `.type` (MIME type) and
    `.read()`.  This signature is compatible with Streamlit's
    `UploadedFile` object and with standard `io.BytesIO` objects,
    making it easy to test without running Streamlit.

    Args:
        uploaded_file: A file-like object with a `.type` attribute
                       containing the MIME type string.

    Returns:
        str: The extracted plain text content of the document.

    Raises:
        ValueError: If the file's MIME type is not supported.
        RuntimeError: If text extraction fails unexpectedly.

    Example:
        >>> text = load_document(st.file_uploader(...))
        >>> print(text[:200])
    """
    mime_type: str = uploaded_file.type
    format_tag: Union[str, None] = _SUPPORTED_TYPES.get(mime_type)

    if format_tag is None:
        supported = ", ".join(_SUPPORTED_TYPES.keys())
        raise ValueError(
            f"Unsupported file type: '{mime_type}'. "
            f"Supported MIME types are: {supported}"
        )

    logger.info("Loading document — MIME type: %s", mime_type)

    try:
        if format_tag == "txt":
            text = _load_txt(uploaded_file)
        elif format_tag == "pdf":
            text = _load_pdf(uploaded_file)
        elif format_tag == "docx":
            text = _load_docx(uploaded_file)
        else:
            # Should never reach here due to the dict guard above
            raise ValueError(f"Unhandled format tag: {format_tag}")

    except Exception as exc:
        logger.exception("Failed to extract text from document.")
        raise RuntimeError(f"Text extraction failed: {exc}") from exc

    extracted_length = len(text.strip())
    logger.info("Document loaded — %d characters extracted.", extracted_length)

    if extracted_length == 0:
        logger.warning("Extracted text is empty. The document may have no readable content.")

    return text
