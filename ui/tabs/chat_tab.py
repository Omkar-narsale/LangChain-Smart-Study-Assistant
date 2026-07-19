"""
ui/tabs/chat_tab.py — Premium ChatGPT-Inspired Chat UI (v3)
============================================================
Improvements v3:
  - Robust "Thinking…" bubble with animated dots (never freezes)
  - Send button disabled during generation
  - Retry once on Groq failures with friendly error
  - Microphone STT via Web Speech API (HTML component)
  - AI response TTS readback per message
  - Auto-scroll to latest message
  - Full chat history in session_state
  - Markdown rendered in AI bubbles via st.markdown
  - Light/dark theme aware bubble colors
"""

from __future__ import annotations
import time
import logging
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from ui.components import render_empty_state

logger = logging.getLogger(__name__)


_SUGGESTED_QUESTIONS = [
    "What is the main topic of this document?",
    "Summarize the key arguments made.",
    "What conclusions does the document draw?",
    "List the most important concepts.",
    "What are the practical applications?",
    "What evidence supports the main claims?",
]


# ---------------------------------------------------------------------------
# Microphone Input HTML Component
# ---------------------------------------------------------------------------

_MIC_HTML = """
<div id="mic-container" style="font-family:'Inter',sans-serif; padding:4px 0;">
    <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
        <button id="mic-btn" onclick="toggleMic()" style="
            background: rgba(124,92,255,0.12);
            border: 1px solid rgba(124,92,255,0.3);
            color: #C7D2FE;
            padding: 9px 16px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.2s;
            display: flex; align-items: center; gap: 6px;
            font-family: 'Inter', sans-serif;
        ">🎤 Start Speaking</button>
        <div id="mic-status" style="font-size:11px;color:#94A3B8;font-weight:500;"></div>
    </div>

    <div id="mic-transcript" style="
        display:none;
        margin-top:10px;
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px;
        padding: 12px 16px;
        font-size: 13.5px;
        color: #F1F5F9;
        line-height: 1.6;
        min-height: 40px;
    "></div>

    <div id="mic-actions" style="display:none;margin-top:10px;display:none;gap:8px;">
        <button id="mic-send" onclick="sendTranscript()" style="
            background: linear-gradient(135deg,#7C5CFF,#9D84FF);
            border: none; color: #fff;
            padding: 8px 18px; border-radius:8px;
            cursor: pointer; font-weight:700; font-size:13px;
            font-family:'Inter',sans-serif;
        ">✓ Use This Text</button>
        <button id="mic-clear" onclick="clearTranscript()" style="
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.1);
            color: #94A3B8; padding: 8px 14px; border-radius:8px;
            cursor:pointer; font-size:13px;font-family:'Inter',sans-serif;
        ">✕ Clear</button>
    </div>
</div>

<script>
let recognition = null;
let listening = false;
let transcript = '';

function toggleMic() {
    if (!('SpeechRecognition' in window) && !('webkitSpeechRecognition' in window)) {
        document.getElementById('mic-status').textContent = '❌ Not supported — please use Chrome or Edge.';
        return;
    }
    if (listening) { recognition.stop(); return; }

    recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
        listening = true;
        const btn = document.getElementById('mic-btn');
        btn.innerHTML = '⏹ Stop';
        btn.style.background = 'rgba(239,68,68,0.12)';
        btn.style.borderColor = 'rgba(239,68,68,0.3)';
        btn.style.color = '#F87171';
        document.getElementById('mic-status').textContent = '🎤 Listening…';
        document.getElementById('mic-transcript').style.display = 'block';
        document.getElementById('mic-transcript').textContent = '…';
        document.getElementById('mic-actions').style.display = 'none';
    };
    recognition.onresult = (event) => {
        transcript = Array.from(event.results).map(r => r[0].transcript).join('');
        document.getElementById('mic-transcript').textContent = transcript;
    };
    recognition.onend = () => {
        listening = false;
        const btn = document.getElementById('mic-btn');
        btn.innerHTML = '🎤 Start Speaking';
        btn.style.background = 'rgba(124,92,255,0.12)';
        btn.style.borderColor = 'rgba(124,92,255,0.3)';
        btn.style.color = '#C7D2FE';
        if (transcript) {
            document.getElementById('mic-status').textContent = '✅ Tap "Use This Text" to send';
            document.getElementById('mic-actions').style.display = 'flex';
        } else {
            document.getElementById('mic-status').textContent = '🔇 No speech detected — try again.';
        }
    };
    recognition.onerror = (e) => {
        listening = false;
        document.getElementById('mic-status').textContent = '❌ Error: ' + e.error;
    };
    recognition.start();
}

function sendTranscript() {
    if (transcript) {
        // Post to parent Streamlit frame
        window.parent.postMessage({type: 'streamlit:setComponentValue', value: transcript}, '*');
        document.getElementById('mic-status').textContent = '📤 Sent to chat input!';
    }
}

function clearTranscript() {
    transcript = '';
    document.getElementById('mic-transcript').style.display = 'none';
    document.getElementById('mic-actions').style.display = 'none';
    document.getElementById('mic-status').textContent = '';
}
</script>
"""


# ---------------------------------------------------------------------------
# Message renderer
# ---------------------------------------------------------------------------

def _render_message(msg: dict, msg_idx: int) -> None:
    role    = msg["role"]
    content = msg["content"]
    ts      = msg.get("timestamp", "")
    is_user = role == "user"

    if is_user:
        st.markdown(f"""
        <div class="chat-message user">
          <div class="chat-avatar avatar-user">👤</div>
          <div style="display:flex;flex-direction:column;align-items:flex-end;">
            <div class="chat-bubble bubble-user">{content}</div>
            <div class="chat-meta">
              <span class="chat-timestamp">{ts}</span>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # AI messages: use st.markdown for proper markdown rendering inside container
        st.markdown(f"""
        <div class="chat-message">
          <div class="chat-avatar avatar-ai">⚡</div>
          <div style="flex:1;min-width:0;">
            <div class="chat-bubble bubble-ai" id="msg-{msg_idx}">
        """, unsafe_allow_html=True)

        # Render content as markdown (supports bold, code, lists)
        st.markdown(content)

        st.markdown(f"""
            </div>
            <div class="chat-meta">
              <span class="chat-timestamp">{ts}</span>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Sources
        sources = msg.get("sources")
        if sources:
            with st.expander(f"📎 {len(sources)} sources used", expanded=False):
                for i, doc in enumerate(sources):
                    chunk_id = doc.metadata.get("chunk", i)
                    page     = doc.metadata.get("page", "—")
                    preview  = doc.page_content.strip()[:220]
                    ellipsis = "…" if len(doc.page_content.strip()) > 220 else ""
                    st.markdown(f"""
                    <div class="source-card">
                      <div class="source-card-header">
                        <span class="source-badge">Source {i+1}</span>
                        <span style="font-size:0.7rem;color:var(--text-secondary);">Chunk #{chunk_id}</span>
                        {f'<span style="font-size:0.7rem;color:var(--text-secondary);">Page {page}</span>' if page != "—" else ""}
                      </div>
                      <div style="color:var(--text-secondary);font-size:0.8rem;line-height:1.55;">{preview}{ellipsis}</div>
                    </div>
                    """, unsafe_allow_html=True)


def _render_thinking() -> None:
    """Render the animated 'Thinking…' bubble."""
    st.markdown("""
    <div class="chat-message" style="animation:chatFadeIn 0.3s ease;">
      <div class="chat-avatar avatar-ai">⚡</div>
      <div class="chat-bubble bubble-ai" style="display:flex;align-items:center;gap:10px;padding:14px 18px;">
        <span style="color:var(--text-secondary);font-size:13px;font-weight:600;">Thinking</span>
        <span style="display:flex;gap:5px;align-items:center;">
          <span class="dot-pulse" style="animation-delay:0s;"></span>
          <span class="dot-pulse" style="animation-delay:0.22s;"></span>
          <span class="dot-pulse" style="animation-delay:0.44s;"></span>
        </span>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Core generation with retry
# ---------------------------------------------------------------------------

def _generate_answer(question: str) -> tuple[str, list]:
    """Call the RAG chain with one retry on failure."""
    from config import invoke_with_retry, task_token_budget
    from rag.rag_chain import _format_context
    from rag.prompts import RAG_PROMPT
    from langchain_core.output_parsers import StrOutputParser

    sources = []
    answer  = ""

    for attempt in range(2):  # retry once
        try:
            retriever = st.session_state.get("rag_retriever")
            if retriever is None:
                return "❌ RAG retriever is not initialized. Please re-upload your document.", []

            sources = invoke_with_retry(retriever, question)
            context = _format_context(sources)
            parser  = StrOutputParser()

            with task_token_budget("rag_answer") as configured_model:
                chain   = RAG_PROMPT | configured_model | parser
                answer  = ""
                for chunk in chain.stream({"context": context, "question": question}):
                    answer += chunk

            return answer.strip(), sources

        except Exception as exc:
            logger.warning(f"Chat attempt {attempt+1} failed: {exc}")
            if attempt == 1:
                return (
                    f"❌ Sorry, I couldn't generate a response after 2 attempts.\n\n"
                    f"**Error:** `{str(exc)[:200]}`\n\n"
                    f"Try rephrasing your question or check your API settings.",
                    [],
                )
            time.sleep(1.5)  # brief pause before retry

    return answer, sources


# ---------------------------------------------------------------------------
# Main tab renderer
# ---------------------------------------------------------------------------

def render_chat_tab() -> None:
    """Render the premium Chat with PDF tab."""
    doc_text = st.session_state.get("document_text", "").strip()

    if not doc_text:
        render_empty_state(
            "💬",
            "Chat with Your Document",
            "Upload a PDF, DOCX, or TXT file on the Dashboard. The RAG pipeline will index it for intelligent Q&A.",
        )
        return

    if st.session_state.get("rag_chain") is None:
        st.markdown("""
        <div style="font-size:13px;color:var(--text-secondary);margin-bottom:12px;font-weight:500;">
          🔄 Building RAG index for your document…
        </div>
        """, unsafe_allow_html=True)
        from rag_pipeline_builder import build_rag_pipeline
        rag_progress = st.progress(0)
        rag_status   = st.empty()
        try:
            build_rag_pipeline(doc_text, rag_progress, rag_status)
        except Exception as exc:
            rag_progress.empty()
            rag_status.empty()
            st.error(f"❌ RAG pipeline build failed: {exc}")
            return
        time.sleep(0.25)
        rag_progress.empty()
        rag_status.empty()
        st.success("✅ Document indexed — ready to chat!")
        st.rerun()

    # ── Header ───────────────────────────────────────────────────────────────
    hdr_col, clear_col = st.columns([5, 1])
    with hdr_col:
        mode = st.session_state.get("inference_mode", "Local Gemma")
        ai_ready = st.session_state.get("rag_chain") is not None
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
          <div style="width:40px;height:40px;border-radius:50%;
                      background:linear-gradient(135deg,var(--primary),var(--accent));
                      display:flex;align-items:center;justify-content:center;
                      font-size:18px;box-shadow:0 4px 14px rgba(124,92,255,0.35);">⚡</div>
          <div>
            <div style="font-size:16px;font-weight:700;color:var(--text-primary);font-family:var(--font-display);">Chat with PDF</div>
            <div style="font-size:11.5px;color:var(--text-secondary);display:flex;align-items:center;gap:6px;margin-top:2px;">
              <span style="width:6px;height:6px;border-radius:50%;background:{'#22C55E' if ai_ready else '#64748B'};display:inline-block;
                           {'animation:statusPulse 2s ease-in-out infinite;' if ai_ready else ''}"></span>
              {mode} · {'RAG Ready' if ai_ready else 'Indexing…'}
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    with clear_col:
        if st.button("🗑 Clear", key="btn_clear_chat", use_container_width=True):
            st.session_state.chat_history  = []
            st.session_state.chat_thinking = False
            st.session_state.pop("pending_chat_answer", None)
            st.session_state.pop("chat_cache", None)
            st.rerun()

    # ── Suggested questions (only when empty) ─────────────────────────────────
    history = st.session_state.get("chat_history", [])
    if not history:
        st.markdown("""
        <div style="font-size:11px;color:var(--text-muted);font-weight:700;
                    text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">
          💡 Suggested Questions
        </div>
        """, unsafe_allow_html=True)
        sug_cols = st.columns(2)
        for i, q in enumerate(_SUGGESTED_QUESTIONS[:4]):
            with sug_cols[i % 2]:
                if st.button(q, key=f"sug_q_{i}", use_container_width=True):
                    st.session_state.pending_chat_question = q
                    st.rerun()

    # ── Chat history ──────────────────────────────────────────────────────────
    st.markdown('<div class="chat-container" id="chat-anchor">', unsafe_allow_html=True)
    for i, msg in enumerate(history):
        _render_message(msg, i)

    # Show thinking indicator if generating
    if st.session_state.get("chat_thinking"):
        _render_thinking()

    st.markdown("</div>", unsafe_allow_html=True)

    # Auto-scroll to bottom
    if history or st.session_state.get("chat_thinking"):
        st.markdown(
            '<script>setTimeout(()=>{const el=document.getElementById("chat-anchor");if(el)el.scrollIntoView({behavior:"smooth",block:"end"});},100);</script>',
            unsafe_allow_html=True,
        )

    # ── Microphone component ──────────────────────────────────────────────────
    with st.expander("🎤 Voice Input (Click to expand)", expanded=False):
        mic_result = components.html(_MIC_HTML, height=150, scrolling=False)
        if mic_result:
            st.session_state.pending_chat_question = str(mic_result)
            st.rerun()

    # ── Input bar ─────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: var(--radius-xl);
        padding: 12px 16px;
        margin-top: 12px;
        backdrop-filter: blur(12px);
    ">
    """, unsafe_allow_html=True)

    is_thinking = st.session_state.get("chat_thinking", False)
    q_col, send_col = st.columns([5, 1])

    with q_col:
        default_q = st.session_state.pop("pending_chat_question", "") or st.session_state.get("rag_question_input", "")
        user_question = st.text_input(
            "Ask a question",
            value=default_q,
            placeholder="Ask anything about your document…",
            label_visibility="collapsed",
            key="chat_input_field",
            disabled=is_thinking,
        )

    with send_col:
        send_clicked = st.button(
            "⏳" if is_thinking else "Send ➤",
            key="btn_send",
            use_container_width=True,
            disabled=is_thinking,
            type="primary",
        )

    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.get("rag_question_input"):
        st.session_state.rag_question_input = ""

    # ── Process new message ───────────────────────────────────────────────────
    if send_clicked and user_question.strip() and not is_thinking:
        question  = user_question.strip()
        timestamp = datetime.now().strftime("%H:%M")

        # Append user message
        st.session_state.chat_history.append({
            "role":      "user",
            "content":   question,
            "sources":   None,
            "timestamp": timestamp,
        })

        # Check cache
        if "chat_cache" not in st.session_state:
            st.session_state.chat_cache = {}

        if question in st.session_state.chat_cache:
            cached = st.session_state.chat_cache[question]
            st.session_state.chat_history.append(cached)
            st.rerun()

        # Set thinking state and rerun to show indicator
        st.session_state.chat_thinking       = True
        st.session_state.pending_chat_answer = question
        st.rerun()

    # ── Process pending answer (after rerun with thinking=True) ───────────────
    if st.session_state.get("chat_thinking") and st.session_state.get("pending_chat_answer"):
        question = st.session_state.pop("pending_chat_answer")
        t0 = time.time()
        try:
            answer, sources = _generate_answer(question)
            elapsed = round(time.time() - t0, 1)
            if "processing_times" not in st.session_state:
                st.session_state.processing_times = {}
            st.session_state.processing_times["Chat"] = elapsed
        except Exception as exc:
            answer  = f"❌ Unexpected error: `{str(exc)[:200]}`"
            sources = []
            elapsed = round(time.time() - t0, 1)
            logger.exception("Chat generation failed.")

        ans_dict = {
            "role":      "assistant",
            "content":   f"{answer}\n\n*⏱ {elapsed}s*",
            "sources":   sources,
            "timestamp": datetime.now().strftime("%H:%M"),
        }
        st.session_state.chat_history.append(ans_dict)
        st.session_state.chat_cache[question] = ans_dict
        st.session_state.chat_thinking = False
        st.rerun()
