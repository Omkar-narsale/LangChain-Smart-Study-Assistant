"""
extract_pdf.py — PDF Text Extractor
===================================
Extracts text from PDFs. Detects scanned pages (if extracted text is too small)
and converts them to images to run OCR.
"""

from __future__ import annotations
import io
import logging

from PyPDF2 import PdfReader
from pdf2image import convert_from_bytes
import streamlit as st

from extractors.ocr_processor import extract_text_from_image_bytes

logger = logging.getLogger(__name__)

def extract_pdf(file: io.IOBase) -> str:
    """
    Extract text from every page of a PDF.
    If a page returns no/little text, it is assumed to be scanned and is passed to OCR.
    """
    raw_bytes = file.read()
    file.seek(0)
    
    reader = PdfReader(file)
    pages: list[str] = []
    
    # We will need the images if we have scanned pages. We lazy-load them to save memory.
    pdf_images = None
    
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        
        # Heuristic: if text is none or extremely short, assume it's scanned
        if not text or len(text.strip()) < 50:
            logger.info("PDF page %d appears to be scanned. Running OCR...", i)
            if pdf_images is None:
                # Convert PDF bytes to PIL Images. This can be slow, so we only do it if needed.
                # Requires poppler installed on the system.
                try:
                    pdf_images = convert_from_bytes(raw_bytes)
                except Exception as exc:
                    logger.warning("Could not convert PDF to images (is poppler installed?). OCR skipped. Error: %s", exc)
                    pdf_images = []
                    
            if pdf_images and i < len(pdf_images):
                # Convert the specific PIL image page to bytes
                img = pdf_images[i]
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                ocr_text = extract_text_from_image_bytes(img_byte_arr.getvalue())
                
                if ocr_text:
                    pages.append(ocr_text)
                    st.session_state["ocr_status"] = "Used"
                else:
                    logger.debug("PDF page %d returned no extractable text from OCR — skipping.", i)
        else:
            pages.append(text.strip())

    return "\n\n".join(pages)
