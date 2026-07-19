"""
floating_chat.py — Floating AI Orb + Chat Drawer
==================================================
Implements a floating circular AI orb fixed to the bottom-right corner of the
Streamlit page.  When clicked (via a Streamlit button hidden beneath the orb)
it toggles a full-featured RAG-backed chat panel built entirely from native
Streamlit components — no extra LLM, no extra model, no extra embeddings.

Public API
----------
    render_floating_ai_chat() -> None
        Call once per page render, AFTER _init_session_state() has run.

Design notes
------------
- The orb itself is a custom HTML/CSS element.  The click-target is a
  transparent Streamlit button positioned over the orb via CSS.
- The chat panel is rendered with native Streamlit components (st.chat_message,
  st.text_input, st.button …) so it participates fully in the re-run cycle.
- All state lives in st.session_state under keys prefixed with "fc_" to avoid
  any collision with the main application state.
- The RAG chain consumed here is the SAME object stored at
  st.session_state.rag_chain — built once by the main app, reused here.
"""

from __future__ import annotations

import logging
import streamlit as st

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Session-state keys (prefixed fc_ → floating chat)
# ---------------------------------------------------------------------------
_FC_OPEN      = "fc_open"        # bool  — panel visible?
_FC_HISTORY   = "fc_history"     # list[dict]  — {role, content, sources}
_FC_INPUT     = "fc_input_val"   # str   — staged input value


def _init_fc_state() -> None:
    """Ensure all floating-chat session-state keys exist."""
    defaults = {
        _FC_OPEN:    False,
        _FC_HISTORY: [],
        _FC_INPUT:   "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ---------------------------------------------------------------------------
# CSS — Orb + Panel + Animations (injected once per render)
# ---------------------------------------------------------------------------

_FLOATING_CSS = """
<style>
/* ================================================================
   FLOATING AI ORB — CSS Variables (local, won't clash with app)
   ================================================================ */
:root {
  --fc-orb-size:    70px;
  --fc-orb-right:   30px;
  --fc-orb-bottom:  30px;
  --fc-panel-w:     420px;
  --fc-panel-h:     650px;
  --fc-z:           99999;
  --fc-accent:      #6366F1;
  --fc-secondary:   #8B5CF6;
  --fc-glow:        rgba(99,102,241,0.45);
  --fc-glow-lg:     rgba(99,102,241,0.65);
  --fc-bg:          rgba(13,13,18,0.92);
  --fc-border:      rgba(255,255,255,0.10);
  --fc-radius:      20px;
  --fc-trans:       0.3s cubic-bezier(0.4,0,0.2,1);
}

/* ================================================================
   ORB WRAPPER
   ================================================================ */
.fc-orb-wrapper {
  position: fixed;
  bottom: var(--fc-orb-bottom);
  right:  var(--fc-orb-right);
  z-index: var(--fc-z);
  width:  var(--fc-orb-size);
  height: var(--fc-orb-size);
}

/* ---- Outer rotating ring ---- */
.fc-orb-ring {
  position: absolute;
  inset: -6px;
  border-radius: 50%;
  border: 2px solid transparent;
  background: conic-gradient(
    from 0deg,
    var(--fc-accent),
    var(--fc-secondary),
    transparent 60%,
    var(--fc-accent)
  ) border-box;
  -webkit-mask:
    linear-gradient(#fff 0 0) padding-box,
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: destination-out;
  mask-composite: exclude;
  animation: fc-ring-spin 3s linear infinite;
}

/* ---- Orb core ---- */
.fc-orb-core {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--fc-accent) 0%, var(--fc-secondary) 100%);
  box-shadow:
    0 0 20px var(--fc-glow),
    0 0 40px rgba(99,102,241,0.25),
    inset 0 1px 0 rgba(255,255,255,0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  cursor: pointer;
  animation: fc-float 3s ease-in-out infinite, fc-breathe 4s ease-in-out infinite;
  transition: transform var(--fc-trans), box-shadow var(--fc-trans);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

/* ---- Particle glow layers ---- */
.fc-orb-core::before {
  content: '';
  position: absolute;
  inset: -8px;
  border-radius: 50%;
  background: radial-gradient(circle, var(--fc-glow) 0%, transparent 70%);
  animation: fc-pulse 2.5s ease-in-out infinite;
  pointer-events: none;
}
.fc-orb-core::after {
  content: '';
  position: absolute;
  inset: -16px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%);
  animation: fc-pulse 2.5s ease-in-out infinite 0.5s;
  pointer-events: none;
}

/* ---- Hover state ---- */
.fc-orb-wrapper:hover .fc-orb-core {
  transform: scale(1.1);
  box-shadow:
    0 0 30px var(--fc-glow-lg),
    0 0 60px rgba(99,102,241,0.35),
    inset 0 1px 0 rgba(255,255,255,0.3);
}
.fc-orb-wrapper:hover .fc-orb-ring {
  animation: fc-ring-spin 1s linear infinite;
}

/* ---- Tooltip ---- */
.fc-tooltip {
  position: absolute;
  right: calc(var(--fc-orb-size) + 12px);
  top: 50%;
  transform: translateY(-50%);
  background: rgba(13,13,18,0.95);
  border: 1px solid var(--fc-border);
  border-radius: 8px;
  padding: 6px 12px;
  font-family: 'Inter', sans-serif;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease;
  backdrop-filter: blur(8px);
}
.fc-tooltip::after {
  content: '';
  position: absolute;
  right: -5px;
  top: 50%;
  transform: translateY(-50%);
  border: 5px solid transparent;
  border-right: 0;
  border-left-color: rgba(13,13,18,0.95);
}
.fc-orb-wrapper:hover .fc-tooltip { opacity: 1; }

/* ---- Hidden Streamlit button over the orb ---- */
.fc-orb-btn-container {
  position: fixed;
  bottom: var(--fc-orb-bottom);
  right:  var(--fc-orb-right);
  z-index: calc(var(--fc-z) + 1);
  width:  var(--fc-orb-size);
  height: var(--fc-orb-size);
}
.fc-orb-btn-container > div,
.fc-orb-btn-container .stButton,
.fc-orb-btn-container .stButton > button {
  width:  var(--fc-orb-size) !important;
  height: var(--fc-orb-size) !important;
  border-radius: 50% !important;
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  color: transparent !important;
  font-size: 0 !important;
  padding: 0 !important;
  margin: 0 !important;
  cursor: pointer !important;
  opacity: 0 !important;
}

/* ================================================================
   CHAT PANEL
   ================================================================ */
.fc-panel-wrapper {
  position: fixed;
  bottom: calc(var(--fc-orb-bottom) + var(--fc-orb-size) + 16px);
  right:  var(--fc-orb-right);
  z-index: var(--fc-z);
  width:  var(--fc-panel-w);
  max-height: var(--fc-panel-h);
  background: var(--fc-bg);
  border: 1px solid var(--fc-border);
  border-radius: var(--fc-radius);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  box-shadow:
    0 24px 80px rgba(0,0,0,0.7),
    0 0 0 1px rgba(255,255,255,0.05),
    0 0 40px rgba(99,102,241,0.12);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: fc-panel-in 0.3s cubic-bezier(0.4,0,0.2,1);
  transform-origin: bottom right;
}

/* ---- Panel Header ---- */
.fc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  background: rgba(255,255,255,0.03);
  border-bottom: 1px solid var(--fc-border);
  flex-shrink: 0;
}
.fc-header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.fc-avatar {
  width: 36px; height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--fc-accent), var(--fc-secondary));
  display: flex; align-items: center; justify-content: center;
  font-size: 18px;
  box-shadow: 0 0 12px var(--fc-glow);
  flex-shrink: 0;
}
.fc-title {
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  font-weight: 700;
  color: #fff;
  letter-spacing: -0.01em;
}
.fc-subtitle {
  font-family: 'Inter', sans-serif;
  font-size: 0.7rem;
  color: rgba(255,255,255,0.45);
  margin-top: 1px;
  display: flex;
  align-items: center;
  gap: 4px;
}
.fc-status-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #10B981;
  animation: fc-dot-pulse 2s ease-in-out infinite;
}
.fc-status-dot.waiting {
  background: #F59E0B;
}
.fc-header-actions {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

/* ---- Model badge ---- */
.fc-model-badge {
  font-family: 'Inter', sans-serif;
  font-size: 0.65rem;
  font-weight: 600;
  color: rgba(99,102,241,0.9);
  background: rgba(99,102,241,0.12);
  border: 1px solid rgba(99,102,241,0.25);
  border-radius: 999px;
  padding: 2px 8px;
  letter-spacing: 0.04em;
}

/* ---- Chat messages area ---- */
.fc-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
  scroll-behavior: smooth;
}
.fc-messages::-webkit-scrollbar { width: 4px; }
.fc-messages::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.12);
  border-radius: 999px;
}

/* ---- Individual message ---- */
.fc-msg {
  display: flex;
  gap: 0.625rem;
  animation: fc-msg-in 0.25s ease;
}
.fc-msg.user { flex-direction: row-reverse; }
.fc-msg-avatar {
  width: 28px; height: 28px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px;
  flex-shrink: 0;
  margin-top: 2px;
}
.fc-msg-avatar.bot  { background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.1); }
.fc-msg-avatar.user { background: linear-gradient(135deg, var(--fc-accent), var(--fc-secondary)); }
.fc-msg-bubble {
  max-width: 78%;
  padding: 0.7rem 0.9rem;
  border-radius: 14px;
  font-family: 'Inter', sans-serif;
  font-size: 0.8125rem;
  line-height: 1.6;
  word-break: break-word;
}
.fc-msg-bubble.bot {
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.09);
  color: rgba(255,255,255,0.88);
  border-bottom-left-radius: 4px;
}
.fc-msg-bubble.user {
  background: linear-gradient(135deg, var(--fc-accent), var(--fc-secondary));
  color: #fff;
  border-bottom-right-radius: 4px;
}

/* ---- Typing indicator ---- */
.fc-typing {
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 0.625rem 0.9rem;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.09);
  border-radius: 14px;
  border-bottom-left-radius: 4px;
  width: fit-content;
}
.fc-typing-dot {
  width: 5px; height: 5px;
  border-radius: 50%;
  background: rgba(255,255,255,0.5);
  animation: fc-bounce 1.4s infinite ease-in-out;
}
.fc-typing-dot:nth-child(2) { animation-delay: 0.2s; }
.fc-typing-dot:nth-child(3) { animation-delay: 0.4s; }

/* ---- Source chips ---- */
.fc-sources {
  margin-top: 0.5rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
}
.fc-source-chip {
  font-family: 'Inter', sans-serif;
  font-size: 0.65rem;
  font-weight: 600;
  color: rgba(99,102,241,0.9);
  background: rgba(99,102,241,0.1);
  border: 1px solid rgba(99,102,241,0.2);
  border-radius: 999px;
  padding: 2px 8px;
  letter-spacing: 0.03em;
}

/* ---- Empty state ---- */
.fc-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  color: rgba(255,255,255,0.3);
  font-family: 'Inter', sans-serif;
  text-align: center;
  padding: 2rem;
}
.fc-empty-icon { font-size: 2.5rem; opacity: 0.6; }
.fc-empty-title { font-size: 0.875rem; font-weight: 600; color: rgba(255,255,255,0.5); }
.fc-empty-sub   { font-size: 0.75rem; line-height: 1.5; max-width: 260px; }

/* ---- Input footer ---- */
.fc-input-row {
  padding: 0.875rem 1rem;
  border-top: 1px solid var(--fc-border);
  background: rgba(255,255,255,0.02);
  flex-shrink: 0;
}
/* Style Streamlit text_input inside the panel */
.fc-input-row [data-testid="stTextInput"] input {
  background: rgba(255,255,255,0.07) !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
  border-radius: 12px !important;
  color: #fff !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 0.8125rem !important;
  padding: 0.625rem 0.875rem !important;
}
.fc-input-row [data-testid="stTextInput"] input::placeholder {
  color: rgba(255,255,255,0.3) !important;
}
.fc-input-row [data-testid="stTextInput"] input:focus {
  border-color: rgba(99,102,241,0.5) !important;
  box-shadow: 0 0 0 2px rgba(99,102,241,0.15) !important;
}
/* Send button */
.fc-input-row .stButton > button {
  background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
  border: none !important;
  border-radius: 10px !important;
  color: #fff !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 0.8rem !important;
  font-weight: 600 !important;
  padding: 0.6rem 1rem !important;
  height: 100% !important;
  transition: all 0.2s ease !important;
}
.fc-input-row .stButton > button:hover {
  opacity: 0.9 !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 16px rgba(99,102,241,0.4) !important;
}
/* Clear + close buttons inside panel */
.fc-action-btn > div > button {
  background: rgba(255,255,255,0.06) !important;
  border: 1px solid rgba(255,255,255,0.1) !important;
  border-radius: 8px !important;
  color: rgba(255,255,255,0.6) !important;
  font-size: 0.75rem !important;
  font-weight: 500 !important;
  padding: 0.3rem 0.6rem !important;
  transition: all 0.2s ease !important;
}
.fc-action-btn > div > button:hover {
  background: rgba(255,255,255,0.1) !important;
  color: #fff !important;
}

/* ================================================================
   KEYFRAME ANIMATIONS
   ================================================================ */
@keyframes fc-float {
  0%, 100% { transform: translateY(0px); }
  50%       { transform: translateY(-6px); }
}
@keyframes fc-breathe {
  0%, 100% { box-shadow: 0 0 20px var(--fc-glow), 0 0 40px rgba(99,102,241,0.25), inset 0 1px 0 rgba(255,255,255,0.25); }
  50%       { box-shadow: 0 0 30px var(--fc-glow-lg), 0 0 60px rgba(99,102,241,0.35), inset 0 1px 0 rgba(255,255,255,0.3); }
}
@keyframes fc-pulse {
  0%, 100% { opacity: 0.6; transform: scale(1); }
  50%       { opacity: 1;   transform: scale(1.08); }
}
@keyframes fc-ring-spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
@keyframes fc-panel-in {
  from { opacity: 0; transform: scale(0.92) translateY(12px); }
  to   { opacity: 1; transform: scale(1) translateY(0); }
}
@keyframes fc-msg-in {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes fc-bounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30%            { transform: translateY(-5px); opacity: 1; }
}
@keyframes fc-dot-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: 0.5; transform: scale(0.8); }
}

/* Make Streamlit not stomp on our fixed elements */
[data-testid="stAppViewContainer"] { overflow: visible !important; }
</style>
"""

# ---------------------------------------------------------------------------
# HTML: The floating orb (purely cosmetic, click intercepted by st.button)
# ---------------------------------------------------------------------------

_ORB_HTML = """
<div class="fc-orb-wrapper" id="fc-orb">
  <div class="fc-orb-ring"></div>
  <div class="fc-orb-core">🤖</div>
  <div class="fc-tooltip">Ask AI</div>
</div>
"""

# ---------------------------------------------------------------------------
# Helper: render one chat message as HTML
# ---------------------------------------------------------------------------

def _msg_html(role: str, content: str, sources: list | None) -> str:
    """Return HTML for a single chat bubble."""
    if role == "user":
        return f"""
<div class="fc-msg user">
  <div class="fc-msg-avatar user">👤</div>
  <div class="fc-msg-bubble user">{content}</div>
</div>"""

    # Build source chips
    source_html = ""
    if sources:
        chips = "".join(
            f'<span class="fc-source-chip">Chunk {doc.metadata.get("chunk", i)}</span>'
            for i, doc in enumerate(sources)
        )
        source_html = f'<div class="fc-sources">{chips}</div>'

    return f"""
<div class="fc-msg bot">
  <div class="fc-msg-avatar bot">🤖</div>
  <div>
    <div class="fc-msg-bubble bot">{content}</div>
    {source_html}
  </div>
</div>"""


# ---------------------------------------------------------------------------
# Status helpers
# ---------------------------------------------------------------------------

def _rag_ready() -> bool:
    return st.session_state.get("rag_chain") is not None


def _doc_uploaded() -> bool:
    return bool(st.session_state.get("document_text", "").strip())


# ---------------------------------------------------------------------------
# Public render function
# ---------------------------------------------------------------------------

def render_floating_ai_chat() -> None:
    """
    Inject the floating AI orb and, when open, the chat panel.

    Call this function exactly once per page render, after session state has
    been initialised.
    """
    _init_fc_state()

    # ── 1. Inject CSS (always) ──────────────────────────────────────────────
    st.markdown(_FLOATING_CSS, unsafe_allow_html=True)

    # ── 2. Inject the visual orb (always) ──────────────────────────────────
    st.markdown(_ORB_HTML, unsafe_allow_html=True)

    # ── 3. Transparent toggle button layered over the orb ──────────────────
    # We use a container with the fc-orb-btn-container class to position the
    # Streamlit button directly over the orb.
    orb_container = st.container()
    with orb_container:
        st.markdown('<div class="fc-orb-btn-container">', unsafe_allow_html=True)
        if st.button("⚡", key="fc_orb_toggle", help="Open AI Chat"):
            st.session_state[_FC_OPEN] = not st.session_state[_FC_OPEN]
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ── 4. Chat panel (only when open) ─────────────────────────────────────
    if not st.session_state[_FC_OPEN]:
        return

    # ── Determine status ───────────────────────────────────────────────────
    doc_ready = _doc_uploaded()
    rag_ready = _rag_ready()

    if not doc_ready:
        status_dot_cls = "waiting"
        status_text    = "No document uploaded"
    elif not rag_ready:
        status_dot_cls = "waiting"
        status_text    = "Preparing document…"
    else:
        status_dot_cls = ""
        status_text    = "AI Ready"

    # ── Panel header ───────────────────────────────────────────────────────
    st.markdown(f"""
<div class="fc-panel-wrapper" id="fc-panel">
  <div class="fc-header">
    <div class="fc-header-left">
      <div class="fc-avatar">🤖</div>
      <div>
        <div class="fc-title">Smart Study Assistant</div>
        <div class="fc-subtitle">
          <span class="fc-status-dot {status_dot_cls}"></span>
          {status_text}
          &nbsp;·&nbsp;
          <span class="fc-model-badge">Gemma 2B</span>
        </div>
      </div>
    </div>
  </div>
""", unsafe_allow_html=True)

    # ── Clear + Close button row ───────────────────────────────────────────
    action_col1, action_col2, _ = st.columns([1, 1, 3])
    with action_col1:
        st.markdown('<div class="fc-action-btn">', unsafe_allow_html=True)
        if st.button("🗑 Clear", key="fc_clear_btn"):
            st.session_state[_FC_HISTORY] = []
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with action_col2:
        st.markdown('<div class="fc-action-btn">', unsafe_allow_html=True)
        if st.button("✕ Close", key="fc_close_btn"):
            st.session_state[_FC_OPEN] = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Chat messages area ─────────────────────────────────────────────────
    history = st.session_state[_FC_HISTORY]

    if not history:
        if not doc_ready:
            empty_msg = "Please upload a document first."
        elif not rag_ready:
            empty_msg = "Preparing your document… please wait."
        else:
            empty_msg = "Ask me anything about your uploaded document!"

        st.markdown(f"""
<div class="fc-empty">
  <div class="fc-empty-icon">🤖</div>
  <div class="fc-empty-title">Smart Study Assistant</div>
  <div class="fc-empty-sub">{empty_msg}</div>
</div>
""", unsafe_allow_html=True)
    else:
        # Render all messages
        messages_html = "\n".join(
            _msg_html(m["role"], m["content"], m.get("sources"))
            for m in history
        )
        st.markdown(
            f'<div class="fc-messages">{messages_html}</div>',
            unsafe_allow_html=True,
        )

    # ── Input row ──────────────────────────────────────────────────────────
    st.markdown('<div class="fc-input-row">', unsafe_allow_html=True)

    input_disabled = not doc_ready or not rag_ready
    placeholder    = (
        "Please upload a document first."   if not doc_ready else
        "Preparing your document…"          if not rag_ready else
        "Ask anything from your uploaded PDF…"
    )

    inp_col, send_col = st.columns([4, 1])
    with inp_col:
        user_q = st.text_input(
            "fc_input",
            value       = st.session_state[_FC_INPUT],
            placeholder = placeholder,
            disabled    = input_disabled,
            label_visibility = "collapsed",
            key         = "fc_text_input",
        )
    with send_col:
        send_clicked = st.button(
            "Send ➤",
            key      = "fc_send_btn",
            disabled = input_disabled,
            use_container_width = True,
        )

    st.markdown('</div>', unsafe_allow_html=True)  # fc-input-row

    # Close panel wrapper div
    st.markdown('</div>', unsafe_allow_html=True)  # fc-panel-wrapper

    # ── Handle send ────────────────────────────────────────────────────────
    if send_clicked and user_q.strip() and rag_ready:
        question = user_q.strip()
        st.session_state[_FC_INPUT] = ""

        # Add user message
        history.append({"role": "user", "content": question, "sources": None})

        # Invoke the shared RAG chain (same object built by main app)
        try:
            result  = st.session_state["rag_chain"].invoke(question)
            answer  = result.get("answer", "Sorry, I could not generate an answer.")
            sources = result.get("sources", [])
        except Exception as exc:
            answer  = f"❌ Error: {exc}"
            sources = []
            logger.exception("Floating chat RAG invocation failed.")

        history.append({"role": "assistant", "content": answer, "sources": sources})
        st.session_state[_FC_HISTORY] = history
        st.rerun()
""
