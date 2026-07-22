"""
ui/upload_section.py — Premium Upload Card + File Information (v3)
==================================================================
Renders the large animated upload area and the rich file info card.

v3:
  - Uses new CSS variable names (glass-card, var(--border), etc.)
  - Cleaner document ready banner
  - Better file info grid layout
  - force_upload=False: hides upload when embedding_status == "ready"
  - force_upload=True:  always shows uploader (Settings page)

v4 (architecture fix):
  - Extracted _reset_document_state() to eliminate duplication
  - Single source of truth for cache clearing
"""

from __future__ import annotations

import hashlib
import logging

import streamlit as st

from ui.components import section_label

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def compute_file_hash(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


def _detect_language(text: str) -> str:
    non_ascii = sum(1 for c in text if ord(c) > 127)
    return "Non-Latin" if (non_ascii / max(len(text), 1)) > 0.30 else "English"


def _detect_doc_type(mime: str, filename: str) -> str:
    # Use extension if MIME is not specific enough
    ext = filename.split('.')[-1].lower() if '.' in filename else ""
    
    mapping = {
        "pdf": "PDF",
        "docx": "DOCX",
        "txt": "TXT",
        "ppt": "PPT",
        "pptx": "PPTX",
        "png": "Image (PNG)",
        "jpg": "Image (JPG)",
        "jpeg": "Image (JPEG)"
    }
    
    return mapping.get(ext, "Unknown")


def _reading_level(word_count: int) -> str:
    if word_count < 500:  return "Basic"
    if word_count < 2000: return "Intermediate"
    return "Advanced"


def _format_bytes(n: int) -> str:
    if n < 1024:       return f"{n} B"
    if n < 1024 ** 2:  return f"{n/1024:.1f} KB"
    return f"{n/1024**2:.2f} MB"


def _reset_document_state() -> None:
    """
    Clear all cached document/RAG state when a new file is detected.

    This is the SINGLE source of truth for cache invalidation.
    Called from both file-upload and text-paste paths.
    """
    st.session_state.parent_docs        = None
    st.session_state.doc_chunks         = None
    st.session_state.doc_embeddings     = None
    st.session_state.rag_vectorstore    = None
    st.session_state.rag_bm25           = None
    st.session_state.rag_retriever      = None
    st.session_state.rag_chain          = None
    st.session_state.embedding_status   = "none"
    st.session_state.chat_history       = []
    st.session_state.chat_cache         = {}
    st.session_state.study_output       = None
    st.session_state.chunk_count        = 0
    st.session_state.processing_times   = {}
    st.session_state.total_process_time = 0
    st.session_state.quiz_submitted     = {}
    st.session_state.quiz_revealed      = {}
    st.session_state.quiz_answers       = {}
    st.session_state.quiz_idx           = 0
    logger.info("All document/RAG caches cleared for new file.")


# ---------------------------------------------------------------------------
# File Info Card (shown after upload)
# ---------------------------------------------------------------------------

def render_file_info_card() -> None:
    """Render the rich document info panel using session state data."""
    name       = st.session_state.get("file_display_name", "")
    words      = st.session_state.get("word_count", 0)
    mins       = st.session_state.get("reading_time", 0)
    pages      = st.session_state.get("page_count", None)
    slides     = st.session_state.get("slide_count", None)
    file_size  = st.session_state.get("file_size", 0)
    doc_type   = st.session_state.get("doc_type", "")
    chunks     = st.session_state.get("chunk_count", 0)
    emb_status = st.session_state.get("embedding_status", "none")
    rag_ready  = st.session_state.get("rag_chain") is not None
    ocr_status = st.session_state.get("ocr_status", "Not Used")

    vector_status = "Ready" if rag_ready else "Pending"
    emb_lbl = {"ready": "Ready", "building": "Building…", "none": "Pending"}.get(emb_status, "Pending")
    emb_color = {
        "Ready": "#22C55E", "Building…": "#00C2FF", "Pending": "#64748B"
    }.get(emb_lbl, "#64748B")
    
    ocr_color = "#22C55E" if ocr_status == "Used" else "#64748B"

    # Determine what to show in the 3rd column of the stats grid
    page_slide_val = "N/A"
    page_slide_lbl = "Pages"
    if pages is not None:
        page_slide_val = str(pages)
        page_slide_lbl = "Pages"
    elif slides is not None:
        page_slide_val = str(slides)
        page_slide_lbl = "Slides"

    st.markdown(f"""
    <div class="glass-card" style="margin-top:20px;">
      <!-- Header row -->
      <div style="display:flex;align-items:center;gap:14px;margin-bottom:18px;">
        <div style="
            width:44px;height:44px;
            background:linear-gradient(135deg,rgba(124,92,255,0.2),rgba(0,194,255,0.1));
            border:1px solid var(--glass-border);
            border-radius:12px;
            display:flex;align-items:center;justify-content:center;
            font-size:20px;flex-shrink:0;
        ">📄</div>
        <div style="flex:1;min-width:0;">
          <div class="text-card-title" style="word-break:break-all;font-size:15px;">{name}</div>
          <div style="font-size:12px;color:var(--text-muted);margin-top:2px;">
            {_format_bytes(file_size)} · {doc_type}
          </div>
        </div>
        {'<div style="font-size:11px;font-weight:700;color:#22C55E;background:rgba(34,197,94,0.1);padding:4px 10px;border-radius:999px;border:1px solid rgba(34,197,94,0.25);white-space:nowrap;">✓ Ready</div>' if rag_ready else ''}
      </div>

      <!-- Stats grid -->
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:14px;">
        <div style="padding:12px;background:rgba(124,92,255,0.06);border:1px solid var(--glass-border);border-radius:10px;text-align:center;">
          <div style="font-size:22px;font-weight:800;color:var(--text-primary);">{words:,}</div>
          <div style="font-size:10px;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.06em;margin-top:2px;">Words</div>
        </div>
        <div style="padding:12px;background:rgba(0,194,255,0.05);border:1px solid var(--glass-border);border-radius:10px;text-align:center;">
          <div style="font-size:22px;font-weight:800;color:var(--text-primary);">{mins}m</div>
          <div style="font-size:10px;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.06em;margin-top:2px;">Read Time</div>
        </div>
        <div style="padding:12px;background:rgba(255,255,255,0.03);border:1px solid var(--glass-border);border-radius:10px;text-align:center;">
          <div style="font-size:22px;font-weight:800;color:var(--text-primary);">{page_slide_val}</div>
          <div style="font-size:10px;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.06em;margin-top:2px;">{page_slide_lbl}</div>
        </div>
        <div style="padding:12px;background:rgba(255,255,255,0.03);border:1px solid var(--glass-border);border-radius:10px;text-align:center;">
          <div style="font-size:22px;font-weight:800;color:var(--text-primary);">{chunks}</div>
          <div style="font-size:10px;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.06em;margin-top:2px;">Chunks</div>
        </div>
      </div>
      
      <!-- System status row -->
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;">
        <div style="padding:12px;background:rgba(255,255,255,0.03);border:1px solid var(--glass-border);border-radius:10px;text-align:center;">
          <div style="font-size:16px;font-weight:700;color:{ocr_color};">{ocr_status}</div>
          <div style="font-size:10px;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.06em;margin-top:2px;">OCR Status</div>
        </div>
        <div style="padding:12px;background:rgba(255,255,255,0.03);border:1px solid var(--glass-border);border-radius:10px;text-align:center;">
          <div style="font-size:16px;font-weight:700;color:{emb_color};">{emb_lbl}</div>
          <div style="font-size:10px;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.06em;margin-top:2px;">Embeddings</div>
        </div>
        <div style="padding:12px;background:rgba(255,255,255,0.03);border:1px solid var(--glass-border);border-radius:10px;text-align:center;">
          <div style="font-size:16px;font-weight:700;color:{'#22C55E' if rag_ready else '#64748B'};">{vector_status}</div>
          <div style="font-size:10px;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.06em;margin-top:2px;">Vector DB</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Upload section renderer
# ---------------------------------------------------------------------------

def render_upload_section(force_upload: bool = False) -> tuple[str, bool]:
    """
    Render the document upload area.
    - If embedding_status == "ready" and not force_upload: show file info card only.
    - Otherwise: show the uploader.
    Returns (document_text, file_changed).
    """
    document     = ""
    file_changed = False

    # ── Already indexed → show info card only (Dashboard) ─────────────────
    if not force_upload and st.session_state.get("embedding_status") == "ready":
        render_file_info_card()
        return document, file_changed

    # ── Show uploader ──────────────────────────────────────────────────────
    if not force_upload:
        section_label("📁", "Upload Document")
        st.markdown(
            '<div class="text-body" style="margin-bottom:16px;">Supported: PDF, PPT, PPTX, DOCX, TXT, PNG, JPG, JPEG · Max 50 MB</div>',
            unsafe_allow_html=True,
        )

    uploaded_files = st.file_uploader(
        "Upload documents",
        type=["txt", "pdf", "docx", "ppt", "pptx", "png", "jpg", "jpeg"],
        label_visibility="collapsed",
        accept_multiple_files=True,
        key="main_uploader" if not force_upload else "settings_uploader",
    )

    if uploaded_files:
        from file_router import load_document
        from PyPDF2 import PdfReader

        all_texts = []
        all_page_texts = []
        total_words = 0
        total_size = 0
        total_pages = 0
        total_slides = 0
        file_names = []
        has_pdf = False
        has_ppt = False

        for uploaded_file in uploaded_files:
            raw_bytes = uploaded_file.read()
            uploaded_file.seek(0)
            file_names.append(uploaded_file.name)
            total_size += len(raw_bytes)

            # PDF page count
            page_count: int | None = None
            if uploaded_file.type == "application/pdf":
                has_pdf = True
                try:
                    uploaded_file.seek(0)
                    reader     = PdfReader(uploaded_file)
                    page_count = len(reader.pages)
                    total_pages += page_count
                    uploaded_file.seek(0)
                except Exception:
                    page_count = 0

            # Extract text
            try:
                document = load_document(uploaded_file)
            except (ValueError, RuntimeError) as exc:
                st.error(f"❌ Could not read the file {uploaded_file.name}: {exc}")
                st.stop()

            all_texts.append(f"--- Document: {uploaded_file.name} ---\n{document}")
            
            # Retrieve page texts from session state pop
            file_pages = st.session_state.pop("page_texts", [document])
            all_page_texts.extend(file_pages)

            if uploaded_file.type in ["application/vnd.ms-powerpoint", "application/vnd.openxmlformats-officedocument.presentationml.presentation"]:
                has_ppt = True
                slides = st.session_state.get("slide_count", 0)
                if slides:
                    total_slides += slides

        # Join everything
        combined_document = "\n\n".join(all_texts)
        words = len(combined_document.split())
        mins = max(1, round(words / 250))
        
        display_name = ", ".join(file_names)
        if len(file_names) > 3:
            display_name = f"{len(file_names)} files ({file_names[0]}, {file_names[1]}...)"

        # Store everything
        st.session_state.document_text     = combined_document
        st.session_state.page_texts        = all_page_texts
        st.session_state.word_count        = words
        st.session_state.reading_time      = mins
        st.session_state.page_count        = total_pages if has_pdf else None
        st.session_state.slide_count       = total_slides if has_ppt else None
        st.session_state.file_display_name = display_name
        st.session_state.file_size         = total_size
        st.session_state.doc_language      = _detect_language(combined_document)
        st.session_state.doc_type          = "Multiple" if len(file_names) > 1 else _detect_doc_type(uploaded_files[0].type, uploaded_files[0].name)
        st.session_state.reading_level     = _reading_level(words)

        new_hash = compute_file_hash(combined_document.encode())
        if new_hash != st.session_state.get("file_hash", ""):
            st.session_state.file_hash = new_hash
            _reset_document_state()
            # Restore state variables
            st.session_state.document_text     = combined_document
            st.session_state.page_texts        = all_page_texts
            st.session_state.word_count        = words
            st.session_state.reading_time      = mins
            st.session_state.page_count        = total_pages if has_pdf else None
            st.session_state.slide_count       = total_slides if has_ppt else None
            st.session_state.file_display_name = display_name
            st.session_state.file_size         = total_size
            st.session_state.doc_language      = _detect_language(combined_document)
            st.session_state.doc_type          = "Multiple" if len(file_names) > 1 else _detect_doc_type(uploaded_files[0].type, uploaded_files[0].name)
            st.session_state.reading_level     = _reading_level(words)
            file_changed = True

    else:
        # Fallback: paste raw text
        st.markdown(
            '<div style="font-size:13px;color:var(--text-secondary);margin-bottom:8px;font-weight:500;margin-top:20px;">Or paste text directly:</div>',
            unsafe_allow_html=True,
        )
        pasted = st.text_area(
            "Paste document text",
            height=120,
            label_visibility="collapsed",
            placeholder="Paste your study material here…",
            key="main_text_area" if not force_upload else "settings_text_area",
        )
        if pasted.strip():
            document = pasted.strip()
            words    = len(document.split())
            mins     = max(1, round(words / 250))
            r_level  = _reading_level(words)
            new_hash = compute_file_hash(document.encode())

            st.session_state.document_text     = document
            st.session_state.word_count        = words
            st.session_state.reading_time      = mins
            st.session_state.page_count        = None
            st.session_state.slide_count       = None
            st.session_state.ocr_status        = "Not Used"
            st.session_state.file_display_name = "Pasted Text"
            st.session_state.file_size         = len(document.encode())
            st.session_state.doc_language      = _detect_language(document)
            st.session_state.doc_type          = "TXT"
            st.session_state.reading_level     = r_level

            if new_hash != st.session_state.get("file_hash", ""):
                st.session_state.file_hash = new_hash
                _reset_document_state()
                file_changed = True

    # Show file info card after upload (but before embedding is done)
    if st.session_state.get("file_display_name") and not st.session_state.get("embedding_status") == "none":
        render_file_info_card()

    return document, file_changed
