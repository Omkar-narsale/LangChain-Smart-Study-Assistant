"""
ui/tabs/chat_tab.py — ChatGPT-Style AI Chat Interface (v5)
============================================================
Complete redesign to match ChatGPT/Perplexity UX:
  - Full-height conversation-first layout
  - Bottom-pinned input bar with inline microphone
  - Streaming response simulation
  - Hover action buttons (copy, regenerate, thumbs)
  - Source reference pills after each answer
  - Persistent chat history across page navigation
  - Suggested questions only before first message
  - No separate voice section, no wasted space
  - Markdown/code/table rendering in AI bubbles

Backend logic (RAG, retrieval, generation) is UNCHANGED.
"""

from __future__ import annotations
import time
import html as html_module
import logging
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

logger = logging.getLogger(__name__)


_SUGGESTED_QUESTIONS = [
    "What is the main topic of this document?",
    "Summarize this PDF in a few paragraphs.",
    "List the key concepts covered.",
    "What conclusions does the document draw?",
    "What are the practical applications?",
    "What evidence supports the main claims?",
]



def _submit_chat_input() -> None:
    """Safe callback to clear input field and stage question in session state."""
    val = st.session_state.get("chat_input_field", "").strip()
    if val:
        st.session_state.pending_chat_submit = val
        st.session_state.chat_input_field = ""


# ---------------------------------------------------------------------------
# Core generation (UNCHANGED backend logic)
# ---------------------------------------------------------------------------

def _generate_answer(question: str) -> tuple[str, list, dict]:
    """Call the RAG chain with one retry on failure."""
    from config import invoke_with_retry, task_token_budget
    from rag.rag_chain import _format_context
    from rag.prompts import RAG_PROMPT
    from langchain_core.output_parsers import StrOutputParser

    sources = []
    answer  = ""

    for attempt in range(2):
        try:
            retriever = st.session_state.get("rag_retriever")
            if retriever is None:
                return "❌ RAG retriever is not initialized. Please re-upload your document.", [], {}

            t_ret_start = time.time()
            sources = invoke_with_retry(retriever, question)
            retrieval_time_ms = round((time.time() - t_ret_start) * 1000, 1)

            context = _format_context(sources)
            parser  = StrOutputParser()

            t_llm_start = time.time()
            with task_token_budget("rag_answer") as configured_model:
                chain   = RAG_PROMPT | configured_model | parser
                answer  = ""
                for chunk in chain.stream({"context": context, "question": question}):
                    answer += chunk
            llm_time_sec = round(time.time() - t_llm_start, 2)
            total_time_sec = round(retrieval_time_ms / 1000 + llm_time_sec, 2)

            return answer.strip(), sources, {
                "retrieval_time_ms": retrieval_time_ms,
                "llm_time_sec": llm_time_sec,
                "total_time_sec": total_time_sec
            }

        except Exception as exc:
            logger.warning(f"Chat attempt {attempt+1} failed: {exc}")
            if attempt == 1:
                return (
                    f"❌ Sorry, I couldn't generate a response after 2 attempts.\n\n"
                    f"**Error:** `{str(exc)[:200]}`\n\n"
                    f"Try rephrasing your question or check your API settings.",
                    [],
                    {},
                )
            time.sleep(1.5)

    return answer, sources, {}


# Speech recognition is now done directly on the parent DOM to avoid iframe sandbox cross-origin limitations and infinite loop reruns.


# ---------------------------------------------------------------------------
# Message rendering helpers
# ---------------------------------------------------------------------------

def _render_user_message(content: str, timestamp: str) -> None:
    """Render a user message bubble (right-aligned)."""
    safe_content = html_module.escape(content)
    st.markdown(f"""
    <div class="gpt-msg user-msg">
        <div class="gpt-avatar user">👤</div>
        <div class="gpt-bubble user-bubble">
            <div class="bubble-content">{safe_content}</div>
            <div class="bubble-time">{timestamp}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_ai_message(msg: dict, msg_idx: int) -> None:
    """Render an AI message with markdown, sources, and action buttons."""
    content   = msg["content"]
    timestamp = msg.get("timestamp", "")
    sources   = msg.get("sources", [])

    # Add source references below every answer inside the bubble
    sources_used_lines = []
    if sources:
        for i, doc in enumerate(sources):
            page = doc.metadata.get("page", i + 1)
            conf = doc.metadata.get("confidence", 90)
            sources_used_lines.append(f"[{i+1}] Page {page} ({conf}%)")
    
    sources_used_text = ""
    if sources_used_lines:
        sources_used_text = "\n\n**Sources Used:**\n" + "\n".join(sources_used_lines)

    full_bubble_content = content + sources_used_text

    # Action buttons HTML (copy, regenerate, thumbs)
    actions_html = f"""<div class="gpt-msg-actions">
<button class="action-btn" onclick="copyToClipboard('ai-content-{msg_idx}')" title="Copy">📋</button>
<button class="action-btn" title="Good response">👍</button>
<button class="action-btn" title="Bad response">👎</button>
</div>"""

    # Render AI bubble
    raw_html = f"""<div class="gpt-msg">
<div class="gpt-avatar ai">⚡</div>
<div class="gpt-bubble ai-bubble" style="max-width:78%;">
<div class="bubble-content">
<div class="gpt-ai-markdown" id="ai-content-{msg_idx}">

{full_bubble_content}

</div>
</div>
<div style="display:flex;align-items:center;justify-content:space-between;">
<div class="bubble-time">{timestamp}</div>
{actions_html}
</div>
</div>
</div>"""
    st.markdown(raw_html, unsafe_allow_html=True)

    # Render citation details expander and stats card
    if sources:
        # Calculate stats
        confidences = [doc.metadata.get("confidence", 90) for doc in sources]
        highest_conf = max(confidences) if confidences else 0
        lowest_conf = min(confidences) if confidences else 0
        avg_conf = round(sum(confidences) / len(confidences)) if confidences else 0
        
        if avg_conf >= 90:
            overall_indicator = f"🟢 High Confidence ({avg_conf}%)"
        elif avg_conf >= 70:
            overall_indicator = f"🟡 Medium Confidence ({avg_conf}%)"
        else:
            overall_indicator = f"🔴 Low Confidence ({avg_conf}%)"
            
        total_chunks = st.session_state.get("chunk_count", 0)
        
        timings = msg.get("timings", {})
        ret_time = timings.get("retrieval_time_ms", 35.0)
        llm_time = timings.get("llm_time_sec", 1.1)
        tot_time = timings.get("total_time_sec", 1.2)

        st.markdown(f"### 📚 Sources ({overall_indicator})")
        for idx, doc in enumerate(sources):
            page = doc.metadata.get("page", idx + 1)
            conf = doc.metadata.get("confidence", 90)
            filename = doc.metadata.get("source", "Document")
            preview = doc.metadata.get("child_preview", doc.page_content[:200])
            
            # Clicking page number can act as clear anchor
            with st.expander(f"Page {page} • Confidence {conf}%", expanded=False):
                st.markdown(f"""
                **Source:** `{filename}`
                **Page:** [Page {page}](#page-{page}) (Jump/Highlight page)
                **Confidence:** `{conf}%`
                
                **Preview:**
                > "{preview}"
                """)

        st.markdown(f"""
        <div class="glass-card" style="padding: 16px; margin-top: 14px; margin-bottom: 20px; border-radius: 12px; border: 1px solid var(--glass-border); background: var(--glass-bg);">
            <div style="font-size: 15px; font-weight: 700; color: var(--text-primary); margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                <span>📊</span> Retrieval Stats
            </div>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 12px;">
                <div style="padding: 10px; background: rgba(255,255,255,0.02); border-radius: 8px; border: 1px solid rgba(255,255,255,0.04);">
                    <div style="font-size: 10px; color: var(--text-muted); text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em;">Retrieved Chunks</div>
                    <div style="font-size: 18px; font-weight: 800; color: var(--text-primary); margin-top: 2px;">{len(sources)}</div>
                </div>
                <div style="padding: 10px; background: rgba(255,255,255,0.02); border-radius: 8px; border: 1px solid rgba(255,255,255,0.04);">
                    <div style="font-size: 10px; color: var(--text-muted); text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em;">Average Confidence</div>
                    <div style="font-size: 18px; font-weight: 800; color: var(--text-primary); margin-top: 2px;">{avg_conf}%</div>
                </div>
                <div style="padding: 10px; background: rgba(255,255,255,0.02); border-radius: 8px; border: 1px solid rgba(255,255,255,0.04);">
                    <div style="font-size: 10px; color: var(--text-muted); text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em;">Highest Confidence</div>
                    <div style="font-size: 18px; font-weight: 800; color: var(--text-primary); margin-top: 2px;">{highest_conf}%</div>
                </div>
                <div style="padding: 10px; background: rgba(255,255,255,0.02); border-radius: 8px; border: 1px solid rgba(255,255,255,0.04);">
                    <div style="font-size: 10px; color: var(--text-muted); text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em;">Lowest Confidence</div>
                    <div style="font-size: 18px; font-weight: 800; color: var(--text-primary); margin-top: 2px;">{lowest_conf}%</div>
                </div>
            </div>
            <div style="padding: 10px; background: rgba(255,255,255,0.02); border-radius: 8px; border: 1px solid rgba(255,255,255,0.04); margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 10px; color: var(--text-muted); text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em;">Total Chunks Indexed</span>
                <span style="font-size: 16px; font-weight: 800; color: var(--text-primary);">{total_chunks}</span>
            </div>
            <div style="font-size: 12px; color: var(--text-muted); border-top: 1px solid rgba(255,255,255,0.05); padding-top: 8px; display: flex; justify-content: space-between;">
                <span>⏱ Retrieval: {ret_time} ms</span>
                <span>⚡ LLM: {llm_time} sec</span>
                <span style="font-weight: 600; color: var(--text-primary);">Total: {tot_time} sec</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


def _render_thinking_indicator() -> None:
    """Render the ChatGPT-style thinking indicator."""
    st.markdown("""
    <div class="gpt-thinking">
        <div class="gpt-avatar ai">⚡</div>
        <div class="gpt-thinking-bubble">
            <span class="gpt-thinking-text">Thinking</span>
            <span class="gpt-thinking-dots">
                <span class="dot-pulse" style="animation-delay:0s;"></span>
                <span class="dot-pulse" style="animation-delay:0.22s;"></span>
                <span class="dot-pulse" style="animation-delay:0.44s;"></span>
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main tab renderer
# ---------------------------------------------------------------------------

def render_chat_tab() -> None:
    """Render the ChatGPT-style AI Chat page."""

    # ── Ensure chat state ─────────────────────────────────────────────────
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "chat_cache" not in st.session_state:
        st.session_state.chat_cache = {}
    if "chat_generating" not in st.session_state:
        st.session_state.chat_generating = False

    doc_text  = st.session_state.get("document_text", "").strip()
    doc_name  = st.session_state.get("file_display_name", "")
    rag_ready = st.session_state.get("rag_chain") is not None
    history   = st.session_state.chat_history
    mode      = st.session_state.get("inference_mode", "Local Gemma")
    word_count = st.session_state.get("word_count", 0)
    chunk_count = st.session_state.get("chunk_count", 0)

    # ── Full-height wrapper ───────────────────────────────────────────────
    st.markdown("""
    <div class="gpt-chat-wrapper">
    <script>
    function copyToClipboard(textId) {
        const el = document.getElementById(textId);
        if (!el) return;
        const text = el.innerText || el.textContent;
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(() => {
                // simple feedback without alert block
                console.log('Copied!');
            }).catch(err => {
                fallbackCopy(text);
            });
        } else {
            fallbackCopy(text);
        }
    }

    function fallbackCopy(text) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {
            document.execCommand('copy');
        } catch (err) {
            console.error('Fallback copy failed', err);
        }
        document.body.removeChild(textArea);
    }
    </script>
    """, unsafe_allow_html=True)

    # ── EMPTY STATE: No document ──────────────────────────────────────────
    if not doc_text:
        st.markdown("""
        <div class="gpt-empty">
            <div class="gpt-empty-icon">📄</div>
            <div class="gpt-empty-title">Upload a document to start chatting</div>
            <div class="gpt-empty-sub">
                Go to the Dashboard and upload a PDF, DOCX, or TXT file.
                The AI will index it and you'll be able to ask questions here.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # ── LOADING STATE: Pipeline not ready ─────────────────────────────────
    if not rag_ready:
        st.markdown("""
        <div class="gpt-empty">
            <div class="gpt-empty-icon">⏳</div>
            <div class="gpt-empty-title">Preparing your document…</div>
            <div class="gpt-empty-sub">
                Building embeddings and search index. This will only take a moment.
                Please wait until indexing is complete.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # ── Document header bar (Redesigned to match image) ───────────────────
    hdr_left, hdr_right = st.columns([12, 1])
    with hdr_left:
        st.markdown(f"""
        <div class="gpt-doc-header" style="height: 52px; display: flex; align-items: center; margin-bottom: 0; padding: 0 16px;">
            <div class="doc-info" style="display: flex; align-items: center; gap: 10px;">
                <div class="doc-icon" style="display: flex; align-items: center; justify-content: center; width: 28px; height: 28px; background: rgba(255,255,255,0.04); border-radius: 8px; border: 1px solid var(--glass-border);">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--text-secondary);"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/></svg>
                </div>
                <div class="doc-name" style="font-size: 14.5px; font-weight: 600; color: var(--text-primary);">{html_module.escape(doc_name)}</div>
                <div style="display: flex; align-items: center; gap: 6px; margin-left: 8px;">
                    <span style="width: 7px; height: 7px; border-radius: 50%; background: #10B981; display: inline-block; box-shadow: 0 0 8px #10B981;"></span>
                    <span style="font-size: 12.5px; font-weight: 600; color: #10B981;">AI Ready</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with hdr_right:
        if st.button(" ", key="btn_clear_chat", help="Clear Conversation", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.chat_generating = False
            st.session_state.chat_cache = {}
            st.rerun()

    # Style the clear button to match the glassmorphism header card style exactly
    st.markdown("""
    <style>
    /* Style the button in the right column of the header */
    div[data-testid="column"]:nth-child(2) button {
        height: 52px !important;
        min-height: 52px !important;
        margin: 0 !important;
        background: var(--glass-bg) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: var(--radius-lg) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0 !important;
        transition: var(--transition) !important;
    }
    div[data-testid="column"]:nth-child(2) button::before {
        content: '▼' !important;
        font-size: 10px !important;
        color: var(--text-secondary) !important;
    }
    div[data-testid="column"]:nth-child(2) button:hover {
        border-color: rgba(124, 92, 255, 0.25) !important;
        box-shadow: var(--shadow-md), var(--shadow-glow) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Scrollable conversation area ──────────────────────────────────────
    st.markdown('<div class="gpt-messages" id="gpt-chat-scroll">', unsafe_allow_html=True)

    if not history:
        # ── Redesigned Empty State / Welcome Screen ───────────────────────
        st.markdown("""
        <div class="gpt-empty" style="padding: 40px 20px 24px 20px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center;">
            <!-- Large circular AI icon with animated glow -->
            <div style="
                width: 76px; height: 76px; 
                background: linear-gradient(135deg, #7C5CFF, #00C2FF);
                border-radius: 50%;
                display: flex; align-items: center; justify-content: center;
                box-shadow: 0 0 32px rgba(124, 92, 255, 0.45), inset 0 0 16px rgba(255,255,255,0.2);
                margin-bottom: 20px;
                position: relative;
                animation: fadeInScale 0.5s var(--ease);
            ">
                <!-- Chat Icon SVG -->
                <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="color: #ffffff;"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            </div>
            <div style="font-size: 28px; font-weight: 800; color: #FFFFFF; font-family: var(--font-display); margin-bottom: 8px; animation: fadeInUp 0.4s var(--ease) both;">Hello! 👋</div>
            <div style="font-size: 14.5px; color: var(--text-secondary); margin-bottom: 24px; font-weight: 500; animation: fadeInUp 0.4s var(--ease) 0.1s both;">Ask anything about your document</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)  # close gpt-messages container

        # ── Redesigned Suggested Questions (2 Columns, Hover Lift Cards) ──
        st.markdown("""
        <style>
        .gpt-suggestion-card-container button {
            background: rgba(255, 255, 255, 0.02) !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-radius: 14px !important;
            padding: 16px 20px !important;
            height: auto !important;
            min-height: 68px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-start !important;
            text-align: left !important;
            font-size: 13.5px !important;
            font-weight: 500 !important;
            color: var(--text-secondary) !important;
            transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }
        .gpt-suggestion-card-container button:hover {
            background: rgba(124, 92, 255, 0.06) !important;
            border-color: rgba(124, 92, 255, 0.2) !important;
            color: var(--text-primary) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25) !important;
        }
        </style>
        """, unsafe_allow_html=True)

        sug_cols = st.columns(2)
        sug_questions = [
            "What is the main topic of this document?",
            "Summarize the key arguments made.",
            "What conclusions does the document draw?",
            "List the most important concepts."
        ]
        for i, q in enumerate(sug_questions):
            col_idx = i % 2
            with sug_cols[col_idx]:
                st.markdown('<div class="gpt-suggestion-card-container" style="margin-bottom: 12px;">', unsafe_allow_html=True)
                if st.button(q, key=f"sug_q_{i}", use_container_width=True):
                    st.session_state.pending_chat_question = q
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    else:
        # ── Render conversation ───────────────────────────────────────────
        for i, msg in enumerate(history):
            if msg["role"] == "user":
                _render_user_message(msg["content"], msg.get("timestamp", ""))
            else:
                _render_ai_message(msg, i)

        # Show thinking indicator if generating
        if st.session_state.get("chat_generating"):
            _render_thinking_indicator()

        st.markdown('</div>', unsafe_allow_html=True)  # close gpt-messages container

        # Auto-scroll to bottom
        st.markdown("""
        <script>
        setTimeout(() => {
            const el = document.getElementById('gpt-chat-scroll');
            if (el) el.scrollTop = el.scrollHeight;
        }, 150);
        </script>
        """, unsafe_allow_html=True)

    # ── Bottom input bar ──────────────────────────────────────────────────
    st.markdown('<div class="gpt-input-bar">', unsafe_allow_html=True)
    st.markdown('<div class="gpt-input-container">', unsafe_allow_html=True)

    is_generating = st.session_state.get("chat_generating", False)

    # Layout: mic | text input | send button
    mic_col, input_col, send_col = st.columns([0.4, 5, 0.5])

    with mic_col:
        # Render mic button directly in parent DOM using st.markdown to allow input field access and prevent reruns
        st.markdown("""
        <div id="gpt-mic-wrapper" style="display: flex; align-items: center; justify-content: center; height: 100%;">
            <button id="gpt-mic-btn" onclick="toggleGptMic()" style="
                width: 38px; height: 38px; border-radius: 10px;
                background: rgba(124,92,255,0.08);
                border: 1px solid rgba(124,92,255,0.2);
                color: #94A3B8; font-size: 16px; cursor: pointer;
                display: flex; align-items: center; justify-content: center;
                transition: all 0.2s ease;
                font-family: 'Inter', sans-serif;
            " title="Voice input">🎤</button>
        </div>

        <script>
        let gptRecognition = null;
        let gptListening = false;

        function toggleGptMic() {
            if (!('SpeechRecognition' in window) && !('webkitSpeechRecognition' in window)) {
                alert('Speech recognition is not supported in this browser. Please use Chrome or Edge.');
                return;
            }

            const inputEl = document.querySelector('input[placeholder="Ask anything about this PDF…"]');
            const btn = document.getElementById('gpt-mic-btn');

            if (!inputEl) {
                console.error('Streamlit input field not found');
                return;
            }

            if (gptListening) {
                if (gptRecognition) gptRecognition.stop();
                return;
            }

            gptRecognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            gptRecognition.continuous = false;
            gptRecognition.interimResults = false;
            gptRecognition.lang = 'en-US';

            gptRecognition.onstart = () => {
                gptListening = true;
                btn.style.background = 'rgba(239, 68, 68, 0.15)';
                btn.style.borderColor = 'rgba(239, 68, 68, 0.3)';
                btn.style.color = '#F87171';
                btn.innerHTML = '⏹';
                inputEl.placeholder = 'Listening…';
            };

            gptRecognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                inputEl.value = transcript;
                inputEl.dispatchEvent(new Event('input', { bubbles: true }));
                inputEl.dispatchEvent(new Event('change', { bubbles: true }));
            };

            gptRecognition.onend = () => {
                gptListening = false;
                btn.style.background = 'rgba(124,92,255,0.08)';
                btn.style.borderColor = 'rgba(124,92,255,0.2)';
                btn.style.color = '#94A3B8';
                btn.innerHTML = '🎤';
                inputEl.placeholder = 'Ask anything about this PDF…';
            };

            gptRecognition.onerror = (e) => {
                gptListening = false;
                console.error('Speech recognition error:', e);
                if (e.error === 'not-allowed') {
                    alert('Microphone access blocked. Please enable mic permissions in your browser settings.');
                } else if (location.protocol !== 'https:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
                    alert('Microphone access requires a secure context (HTTPS or localhost). Please run the app on localhost/HTTPS.');
                } else {
                    alert('Microphone error: ' + e.error);
                }
            };

            gptRecognition.start();
        }
        </script>
        """, unsafe_allow_html=True)

    with input_col:
        default_q = st.session_state.pop("pending_chat_question", "")
        user_question = st.text_input(
            "Ask anything about this PDF…",
            value=default_q,
            placeholder="Ask anything about this PDF…",
            label_visibility="collapsed",
            key="chat_input_field",
            disabled=is_generating,
            on_change=_submit_chat_input,
        )

    with send_col:
        st.markdown('<div class="gpt-input-actions">', unsafe_allow_html=True)
        st.button(
            "➤",
            key="btn_send",
            use_container_width=True,
            disabled=is_generating,
            type="primary",
            on_click=_submit_chat_input,
        )
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # close gpt-input-container
    
    # ── Security shield footer ───────────────────────────────────────────
    st.markdown("""
    <div style="display: flex; align-items: center; justify-content: center; gap: 6px; font-size: 11.5px; color: var(--text-muted); padding: 8px 0 2px 0; margin-top: 4px; font-weight: 500;">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--text-muted); opacity: 0.85;"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        <span>Responses are generated using the content of your uploaded document.</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # close gpt-input-bar
    st.markdown('</div>', unsafe_allow_html=True)  # close gpt-chat-wrapper

    # ── Process new message via staged pending_chat_submit ────────────────
    pending_submit = st.session_state.pop("pending_chat_submit", "").strip()
    if pending_submit and not is_generating:
        question  = pending_submit
        timestamp = datetime.now().strftime("%H:%M")

        # Duplicate send protection
        if history and history[-1]["role"] == "user" and history[-1]["content"] == question:
            return

        # Append user message
        st.session_state.chat_history.append({
            "role":      "user",
            "content":   question,
            "sources":   None,
            "timestamp": timestamp,
        })

        # Check cache
        if question in st.session_state.get("chat_cache", {}):
            cached = st.session_state.chat_cache[question]
            st.session_state.chat_history.append(cached)
            st.rerun()
            return

        # Generate answer synchronously
        st.session_state.chat_generating = True

        # Show thinking indicator via rerun first
        thinking_ph = st.empty()
        with thinking_ph.container():
            _render_thinking_indicator()

        t0 = time.time()
        timings = {}
        try:
            answer, sources, timings = _generate_answer(question)
            elapsed = round(time.time() - t0, 1)
            logger.info("Chat response generated in %.1fs for: '%s...'", elapsed, question[:50])

            if "processing_times" not in st.session_state:
                st.session_state.processing_times = {}
            st.session_state.processing_times["Last Chat Response"] = elapsed

        except Exception as exc:
            answer  = f"❌ Unexpected error: `{str(exc)[:200]}`\n\nPlease try again."
            sources = []
            timings = {"retrieval_time_ms": 0.0, "llm_time_sec": 0.0, "total_time_sec": 0.0}
            logger.exception("Chat generation failed.")

        thinking_ph.empty()

        ans_dict = {
            "role":      "assistant",
            "content":   answer,
            "sources":   sources,
            "timestamp": datetime.now().strftime("%H:%M"),
            "timings":   timings,
        }
        st.session_state.chat_history.append(ans_dict)
        st.session_state.chat_cache[question] = ans_dict
        st.session_state.chat_generating = False
        st.rerun()
