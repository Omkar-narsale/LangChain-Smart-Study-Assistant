"""
app.py — Smart Study Assistant (Premium Edition v3)
====================================================
Entry point. Responsibilities:
  1. Inject global CSS (ui/styles.py)
  2. Render sidebar (ui/sidebar_panel.py)
  3. Top Navigation & Routing
  4. Core Workspace (Upload + Output Panel)

v3 improvements:
  - All session state keys pre-initialized (prevents KeyError)
  - 4-stage animated progress for study material generation
  - Theme initialized before CSS injection
  - Dashboard hides upload correctly after doc load
"""

from __future__ import annotations

import time
import logging
from datetime import datetime

import streamlit as st

# ── Backend imports ──────────────────────────────────────────────────────────
from chains import build_study_chain
from rag_pipeline_builder import build_rag_pipeline

# ── UI imports ───────────────────────────────────────────────────────────────
from ui.styles import get_css
from ui.components import (
    render_navbar,
    render_hero,
    render_feature_grid,
    render_time_badge,
    section_label,
)
from ui.upload_section import render_upload_section
from ui.sidebar_panel import render_sidebar
from ui.tabs.summary_tab import render_summary_tab
from ui.tabs.keypoints_tab import render_keypoints_tab
from ui.tabs.quiz_tab import render_quiz_tab
from ui.tabs.flashcards_tab import render_flashcards_tab
from ui.tabs.chat_tab import render_chat_tab
from ui.tabs.exam_tab import render_exam_tab
from mindmap_renderer import render_mindmap_tab

logger = logging.getLogger(__name__)

# ===========================================================================
# ── Page Configuration (must be the very first Streamlit call) ─────────────
# ===========================================================================

st.set_page_config(
    page_title="Smart Study Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ===========================================================================
# ── Session State Initialization ────────────────────────────────────────────
# ===========================================================================

def _init_session_state() -> None:
    """Initialize all session state keys with safe defaults."""
    defaults = {
        # Navigation
        "current_page":       "dashboard",
        # Theme (initialize before CSS injection)
        "theme":              "dark",
        # Document
        "document_text":      "",
        "file_hash":          "",
        "file_display_name":  "",
        "file_size":          0,
        "word_count":         0,
        "reading_time":       0,
        "page_count":         None,
        "slide_count":        None,
        "doc_language":       "English",
        "doc_type":           "",
        "reading_level":      "",
        "ocr_status":         "Not Used",
        # RAG pipeline
        "doc_chunks":         None,
        "doc_embeddings":     None,
        "rag_vectorstore":    None,
        "rag_retriever":      None,
        "rag_chain":          None,
        "embedding_status":   "none",
        "chunk_count":        0,
        # Chat
        "chat_history":       [],
        "chat_thinking":      False,
        "pending_chat_answer": None,
        "rag_question_input": "",
        # Study output
        "study_output":       None,
        "processing_times":   {},
        "total_process_time": 0,
        # Flashcards
        "fc_idx":             0,
        "fc_order":           [],
        # Quiz
        "quiz_idx":           0,
        "quiz_submitted":     {},
        "quiz_revealed":      {},
        "quiz_answers":       {},
        "quiz_done":          False,
        # Exam Generator
        "exam_questions":     {},
        # Inference
        "inference_mode":     "Local Gemma",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

_init_session_state()

# ===========================================================================
# ── Inject Global CSS ───────────────────────────────────────────────────────
# ===========================================================================

st.markdown(get_css(), unsafe_allow_html=True)

# ===========================================================================
# ── Sidebar & Top Nav ───────────────────────────────────────────────────────
# ===========================================================================

render_sidebar()
render_navbar()

current_page = st.session_state.get("current_page", "dashboard")

# ===========================================================================
# ── Helper: 4-Stage Progress Indicator ─────────────────────────────────────
# ===========================================================================

def _run_rag_with_progress(doc_text: str) -> bool:
    """Build RAG pipeline with a 4-stage animated progress UI. Returns success."""
    progress_ph = st.empty()
    status_ph   = st.empty()

    stages = [
        (10, "⚙️  Preparing document…"),
        (40, "🔍  Chunking & embedding…"),
        (80, "🗄️  Building vector store…"),
        (100, "✅  Document ready!"),
    ]

    try:
        prog_bar = progress_ph.progress(0)
        for pct, msg in stages[:-1]:
            status_ph.markdown(
                f'<p style="color:var(--text-secondary);font-size:13px;font-weight:500;">{msg}</p>',
                unsafe_allow_html=True,
            )
            build_rag_pipeline(st.session_state.document_text, prog_bar, st.empty())
            prog_bar.progress(pct)
            break  # build_rag_pipeline handles its own progress

        # Let it finish
        prog_bar.progress(100)
        status_ph.markdown(
            '<p style="color:var(--success);font-size:13px;font-weight:600;">✅ Document indexed and ready!</p>',
            unsafe_allow_html=True,
        )
        time.sleep(0.8)
        return True
    except Exception as exc:
        progress_ph.empty()
        status_ph.empty()
        st.error(f"❌ Indexing failed: {exc}")
        return False
    finally:
        progress_ph.empty()
        status_ph.empty()


def _run_study_generation() -> None:
    """Run study material generation with a 4-stage animated progress display."""
    doc_text = st.session_state.get("document_text", "").strip()

    if not doc_text:
        st.warning("⚠️ Please upload a document on the Dashboard first.")
        st.stop()

    if st.session_state.get("embedding_status") != "ready":
        st.warning("⚠️ Document is still processing. Please wait.")
        st.stop()

    # 4-stage progress UI
    progress_container = st.container()
    with progress_container:
        stage_ph  = st.empty()
        bar_ph    = st.empty()

        def _update_stage(pct: int, msg: str) -> None:
            stage_ph.markdown(f"""
            <div style="
                background: var(--glass-bg);
                border: 1px solid var(--glass-border);
                border-radius: var(--radius-lg);
                padding: 16px 20px;
                display: flex;
                align-items: center;
                gap: 12px;
                backdrop-filter: blur(12px);
            ">
                <span style="font-size:1.2rem;">{msg.split()[0]}</span>
                <div>
                    <div style="font-size:13px;font-weight:700;color:var(--text-primary);">{' '.join(msg.split()[1:])}</div>
                    <div style="font-size:11px;color:var(--text-muted);margin-top:2px;">{pct}% complete</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            bar_ph.progress(pct)

        _update_stage(5,  "📋 Preparing document context…")
        time.sleep(0.3)
        _update_stage(15, "🤖 Initializing AI model…")
        time.sleep(0.3)

        t0 = time.time()
        chain = build_study_chain()

        _update_stage(30, "✍️ Generating study material…")

        try:
            out = chain.invoke({"document": doc_text})
            _update_stage(90, "🗂️ Formatting results…")
            time.sleep(0.3)

            st.session_state.study_output       = out
            st.session_state.total_process_time = round(time.time() - t0, 3)
            st.session_state.quiz_submitted      = {}
            st.session_state.quiz_revealed       = {}
            st.session_state.quiz_answers        = {}
            st.session_state.quiz_done           = False
            st.session_state.quiz_idx            = 0
            st.session_state.fc_idx              = 0
            st.session_state.fc_order            = []

            _update_stage(100, "🎉 Study material ready!")
            time.sleep(0.6)

        except Exception as exc:
            stage_ph.empty()
            bar_ph.empty()
            st.error(f"❌ Generation failed: {exc}")
            return
        finally:
            stage_ph.empty()
            bar_ph.empty()

    st.rerun()


# ===========================================================================
# ── Routing ─────────────────────────────────────────────────────────────────
# ===========================================================================

if current_page == "dashboard":
    st.markdown("<h2 class='text-section'>Dashboard</h2>", unsafe_allow_html=True)
    document, file_changed = render_upload_section()

    if file_changed and st.session_state.get("document_text"):
        success = _run_rag_with_progress(st.session_state.document_text)
        if success:
            st.rerun()

    if st.session_state.get("embedding_status") == "ready":
        # Show a clean "ready" banner below the document card
        st.markdown("""
        <div style="
            margin-top: 16px;
            background: rgba(34,197,94,0.08);
            border: 1px solid rgba(34,197,94,0.25);
            border-radius: var(--radius-lg);
            padding: 14px 20px;
            display: flex;
            align-items: center;
            gap: 12px;
            animation: fadeInUp 0.4s ease;
        ">
            <span style="font-size:1.3rem;">✅</span>
            <div>
                <div style="font-size:14px;font-weight:700;color:#4ade80;">Document Ready</div>
                <div style="font-size:12px;color:var(--text-secondary);margin-top:2px;">
                    Choose a feature from the sidebar to start studying.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

elif current_page == "chat":
    render_chat_tab()

elif current_page == "settings":
    st.markdown("<h2 class='text-section'>Settings</h2>", unsafe_allow_html=True)
    st.markdown("<p class='text-body'>Configure your AI and application preferences.</p>", unsafe_allow_html=True)

    st.markdown("<h3 class='text-card-title' style='margin-top:24px;'>Inference Mode</h3>", unsafe_allow_html=True)
    mode = st.radio(
        "Select Model",
        ["Local Gemma", "Groq API"],
        index=0 if st.session_state.get("inference_mode", "Local Gemma") == "Local Gemma" else 1,
        label_visibility="collapsed"
    )
    st.session_state.inference_mode = mode

    st.markdown("<h3 class='text-card-title' style='margin-top:32px;'>Upload Another Document</h3>", unsafe_allow_html=True)
    st.markdown("<p class='text-body'>Replace the current document with a new one.</p>", unsafe_allow_html=True)
    document, file_changed = render_upload_section(force_upload=True)
    if file_changed and st.session_state.get("document_text"):
        progress_ph = st.empty()
        prog_bar    = progress_ph.progress(0)
        status_ph   = st.empty()
        try:
            build_rag_pipeline(st.session_state.document_text, prog_bar, status_ph)
            prog_bar.progress(100)
            status_ph.markdown(
                '<p style="color:var(--success);font-size:13px;font-weight:600;">✅ Document Ready!</p>',
                unsafe_allow_html=True,
            )
            time.sleep(0.8)
            st.session_state.current_page = "dashboard"
            st.rerun()
        except Exception as exc:
            st.error(f"❌ RAG Indexing failed: {exc}")
        finally:
            progress_ph.empty()
            status_ph.empty()

elif current_page == "study":
    st.markdown("<h2 class='text-section'>Study Notes</h2>", unsafe_allow_html=True)
    if not st.session_state.get("study_output"):
        st.markdown("""
        <div style="
            background: var(--glass-bg);
            border: 1px solid var(--glass-border);
            border-radius: var(--radius-xl);
            padding: 32px;
            text-align: center;
            margin-bottom: 24px;
            backdrop-filter: blur(12px);
        ">
            <div style="font-size:2.5rem;margin-bottom:12px;">📚</div>
            <div style="font-size:18px;font-weight:700;color:var(--text-primary);margin-bottom:6px;">
                No Study Material Generated
            </div>
            <div style="font-size:14px;color:var(--text-secondary);max-width:400px;margin:0 auto 20px;">
                Click the button below to generate a complete study package from your uploaded document.
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            generate_clicked = st.button(
                "🚀 Generate Study Material",
                type="primary",
                use_container_width=True,
            )

        if generate_clicked:
            _run_study_generation()
    else:
        study_out = st.session_state.get("study_output")
        render_summary_tab(study_out)

elif current_page == "key_points":
    st.markdown("<h2 class='text-section'>Key Points</h2>", unsafe_allow_html=True)
    if not st.session_state.get("study_output"):
        st.warning("Generate Study Material first on the Study Notes page.")
    else:
        render_keypoints_tab(st.session_state.study_output)

elif current_page == "flashcards":
    st.markdown("<h2 class='text-section'>Flashcards</h2>", unsafe_allow_html=True)
    if not st.session_state.get("study_output"):
        st.warning("Generate Study Material first on the Study Notes page.")
    else:
        render_flashcards_tab(st.session_state.study_output)

elif current_page == "quiz":
    st.markdown("<h2 class='text-section'>Quiz</h2>", unsafe_allow_html=True)
    if not st.session_state.get("study_output"):
        st.warning("Generate Study Material first on the Study Notes page.")
    else:
        render_quiz_tab(st.session_state.study_output)

elif current_page == "exam":
    if not st.session_state.get("study_output"):
        st.markdown("<h2 class='text-section'>🎓 Bloom's Taxonomy Exam Generator</h2>", unsafe_allow_html=True)
        st.warning("Generate Study Material first on the Study Notes page.")
    else:
        render_exam_tab(st.session_state.study_output)

elif current_page == "mind_map":
    render_mindmap_tab()


# ===========================================================================
# ── Footer & Download Report ────────────────────────────────────────────────
# ===========================================================================

if st.session_state.get("study_output") and current_page in ["study", "flashcards", "quiz", "key_points"]:
    out    = st.session_state.study_output
    times  = st.session_state.get("processing_times", {})
    total_t = st.session_state.get("total_process_time", 0)
    name   = st.session_state.get("file_display_name", "Document")
    words  = st.session_state.get("word_count", 0)
    mins   = st.session_state.get("reading_time", 0)
    pages  = st.session_state.get("page_count")
    chunks = st.session_state.get("chunk_count", 0)
    lang   = st.session_state.get("doc_language", "—")
    level  = st.session_state.get("reading_level", "—")
    gen_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    st.markdown('<div style="height:1px;background:var(--border);margin:48px 0 24px;"></div>', unsafe_allow_html=True)

    timing_lines = "\n".join(f"  {k}: {v}s" for k, v in times.items())

    kp_raw = out.get("key_points", [])
    kp_text = "\n".join(f"{i+1}. {p}" for i, p in enumerate(kp_raw) if p) if isinstance(kp_raw, list) else str(kp_raw)

    fc_raw = out.get("flashcards", [])
    fc_text = "\n\n".join(f"Q: {c.get('front','')}\nA: {c.get('back','')}" for c in fc_raw if isinstance(c, dict)) if isinstance(fc_raw, list) else str(fc_raw)

    qz_raw = out.get("quiz", {})
    qz_parts = []
    if isinstance(qz_raw, dict):
        for item in qz_raw.get("mcq", []):
            qz_parts.append(f"Q: {item.get('question','')}\nOptions: {', '.join(item.get('options',[]))}\nA: {item.get('answer','')}")
        for item in qz_raw.get("fill_blank", []):
            qz_parts.append(f"Q: {item.get('question','')}\nA: {item.get('answer','')}")
        for item in qz_raw.get("true_false", []):
            qz_parts.append(f"Q: {item.get('question','')}\nA: {item.get('answer','')}")
        for item in qz_raw.get("short_answer", []):
            qz_parts.append(f"Q: {item.get('question','')}\nA: {item.get('answer','')}")
    qz_text = "\n\n".join(qz_parts) if qz_parts else str(qz_raw)

    report = f"""SMART STUDY REPORT
{'='*65}
Generated: {gen_ts}

📋 DOCUMENT INFO
{'-'*40}
File:           {name}
Words:          {words:,}
Reading Time:   {mins} minutes
Pages:          {pages if pages else "N/A"}
Chunks:         {chunks}
Language:       {lang}
Reading Level:  {level}

⏱ PROCESSING TIMES
{'-'*40}
{timing_lines}
  Total: {total_t}s

📄 SUMMARY
{'-'*40}
{out.get('summary', '')}

📌 KEY POINTS
{'-'*40}
{kp_text}

📝 QUIZ
{'-'*40}
{qz_text}

🃏 FLASHCARDS
{'-'*40}
{fc_text}

{'='*65}
Generated by Smart Study Assistant
"""

    st.download_button(
        label="⬇ Download Full Study Report",
        data=report,
        file_name="Study_Report.txt",
        mime="text/plain",
        use_container_width=True,
    )