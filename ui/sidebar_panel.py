"""
ui/sidebar_panel.py — Premium Glassmorphism Sidebar (v3)
=========================================================
Renders a frosted sidebar with navigation, status cards, and privacy badge.

v3 improvements:
  - Active nav item highlighted with gradient accent
  - Smooth hover animations via CSS injection
  - Better status card with animated dots
  - Compact file info in sidebar
  - Model name display
"""

from __future__ import annotations

import streamlit as st


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

def _sidebar_nav_link(icon: str, label: str, page_id: str) -> None:
    """Render a sidebar navigation link button."""
    is_active = st.session_state.get("current_page", "dashboard") == page_id

    if is_active:
        st.markdown(f"""
        <div style="
            background: linear-gradient(90deg, rgba(124,92,255,0.18), rgba(124,92,255,0.06));
            border: 1px solid rgba(124,92,255,0.25);
            border-radius: var(--radius-md);
            padding: 9px 14px;
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
            font-weight: 700;
            color: var(--text-primary);
            cursor: default;
        ">
            <span style="font-size:15px;">{icon}</span>
            <span>{label}</span>
            <span style="margin-left:auto;width:5px;height:5px;border-radius:50%;
                         background:var(--primary);box-shadow:0 0 8px var(--primary);"></span>
        </div>
        """, unsafe_allow_html=True)
    else:
        if st.button(f"{icon}  {label}", key=f"nav_{page_id}", use_container_width=True):
            st.session_state.current_page = page_id
            st.rerun()


def _sidebar_row(label: str, value: str) -> None:
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;font-size:12px;padding:5px 0;
                border-bottom:1px solid var(--border-soft);">
      <span style="color:var(--text-muted);">{label}</span>
      <span style="color:var(--text-primary);font-weight:600;">{value}</span>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main sidebar renderer
# ---------------------------------------------------------------------------

def render_sidebar() -> None:
    """Populate the Streamlit sidebar."""
    with st.sidebar:
        # ── Logo & Title ──────────────────────────────────────────────────
        st.markdown("""
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:28px;padding-bottom:16px;
                    border-bottom:1px solid var(--border);">
          <div style="width:38px;height:38px;
                      background:linear-gradient(135deg,var(--primary),var(--accent));
                      border-radius:10px;
                      display:flex;align-items:center;justify-content:center;
                      color:#fff;font-size:18px;
                      box-shadow:0 4px 14px rgba(124,92,255,0.35);
                      flex-shrink:0;">⚡</div>
          <div>
            <div style="font-family:var(--font-display);font-weight:800;font-size:15px;
                        letter-spacing:-0.02em;color:var(--text-primary);">SmartStudy</div>
            <div style="color:var(--text-muted);font-size:11px;font-weight:500;
                        letter-spacing:0.04em;text-transform:uppercase;">AI Assistant</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Navigation label ──────────────────────────────────────────────
        st.markdown("""
        <div style="font-size:10.5px;font-weight:700;color:var(--text-muted);
                    text-transform:uppercase;letter-spacing:0.07em;
                    margin-bottom:8px;">Navigation</div>
        """, unsafe_allow_html=True)

        # ── Navigation items ──────────────────────────────────────────────
        _sidebar_nav_link("🏠", "Dashboard",   "dashboard")
        _sidebar_nav_link("📝", "Study Notes", "study")
        _sidebar_nav_link("⭐", "Key Points",  "key_points")
        _sidebar_nav_link("🧠", "Flashcards",  "flashcards")
        _sidebar_nav_link("❓", "Quiz",        "quiz")
        _sidebar_nav_link("🎓", "Exam Generator", "exam")
        _sidebar_nav_link("💬", "AI Chat",     "chat")
        _sidebar_nav_link("🗺", "Mind Map",    "mind_map")
        _sidebar_nav_link("⚙", "Settings",    "settings")

        st.markdown('<div class="sidebar-divider" style="margin:16px 0;"></div>', unsafe_allow_html=True)

        # ── System Status Card ────────────────────────────────────────────
        st.markdown("""
        <div style="font-size:10.5px;font-weight:700;color:var(--text-muted);
                    text-transform:uppercase;letter-spacing:0.07em;margin-bottom:10px;">
            System Status
        </div>
        """, unsafe_allow_html=True)

        emb_status = st.session_state.get("embedding_status", "none")
        study_out  = st.session_state.get("study_output")
        rag_ready  = st.session_state.get("rag_chain") is not None
        mode       = st.session_state.get("inference_mode", "Local Gemma")

        model_active = bool(study_out or rag_ready)
        model_lbl    = "Active" if model_active else "Idle"
        model_cls    = "status-ready" if model_active else "status-none"
        model_dot    = "dot-green" if model_active else "dot-gray"

        emb_lbl = {"ready": "Ready", "building": "Building…", "none": "Pending"}.get(emb_status, "Pending")
        emb_cls = {"ready": "status-ready", "building": "status-building", "none": "status-none"}.get(emb_status, "status-none")
        emb_dot = {"ready": "dot-green", "building": "dot-yellow", "none": "dot-gray"}.get(emb_status, "dot-gray")

        faiss_lbl = "Indexed" if rag_ready else "None"
        faiss_cls = "status-ready" if rag_ready else "status-none"
        faiss_dot = "dot-green" if rag_ready else "dot-gray"

        chunk_count = st.session_state.get("chunk_count", 0)

        st.markdown(f"""
        <div class="bento-card" style="padding:14px;gap:9px;border-radius:var(--radius-md);">
          <div style="font-size:11px;color:var(--text-muted);font-weight:600;margin-bottom:4px;">
            Mode: <span style="color:var(--text-secondary);">{mode}</span>
          </div>
          <div style="display:flex;justify-content:space-between;font-size:12px;align-items:center;">
            <span style="color:var(--text-secondary);">Model</span>
            <span class="status-chip {model_cls}">
              <span class="dot {model_dot}"></span> {model_lbl}
            </span>
          </div>
          <div style="display:flex;justify-content:space-between;font-size:12px;align-items:center;">
            <span style="color:var(--text-secondary);">Embeddings</span>
            <span class="status-chip {emb_cls}">
              <span class="dot {emb_dot}"></span> {emb_lbl}
            </span>
          </div>
          <div style="display:flex;justify-content:space-between;font-size:12px;align-items:center;">
            <span style="color:var(--text-secondary);">Vector Store</span>
            <span class="status-chip {faiss_cls}">
              <span class="dot {faiss_dot}"></span> {faiss_lbl}
            </span>
          </div>
          {f'<div style="font-size:11px;color:var(--text-muted);margin-top:2px;">Chunks indexed: {chunk_count}</div>' if chunk_count else ''}
        </div>
        """, unsafe_allow_html=True)

        # ── Compact document info (if loaded) ─────────────────────────────
        doc_name = st.session_state.get("file_display_name", "")
        if doc_name and rag_ready:
            words  = st.session_state.get("word_count", 0)
            mins   = st.session_state.get("reading_time", 0)
            ocr    = st.session_state.get("ocr_status", "Not Used")
            slides = st.session_state.get("slide_count", None)
            
            extra_info = ""
            if slides is not None:
                extra_info = f" · {slides} slides"
            elif ocr == "Used":
                extra_info = f" · OCR Used"

            st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div style="font-size:10.5px;font-weight:700;color:var(--text-muted);
                        text-transform:uppercase;letter-spacing:0.07em;margin-bottom:8px;">
                Document
            </div>
            <div style="background:rgba(34,197,94,0.06);border:1px solid rgba(34,197,94,0.18);
                        border-radius:var(--radius-md);padding:10px 12px;font-size:12px;">
                <div style="font-weight:600;color:var(--text-primary);margin-bottom:4px;
                            word-break:break-all;font-size:11.5px;">📄 {doc_name}</div>
                <div style="color:var(--text-muted);">{words:,} words · {mins} min read{extra_info}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

        # ── Privacy Badge ─────────────────────────────────────────────────
        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;
                    padding:12px 14px;
                    background:rgba(34,197,94,0.05);
                    border:1px solid rgba(34,197,94,0.15);
                    border-radius:var(--radius-md);
                    font-size:11.5px;color:var(--text-secondary);">
          <span style="font-size:16px;">🔒</span>
          <div>
            <div style="font-weight:700;color:var(--text-primary);margin-bottom:1px;">Privacy First</div>
            <div style="color:var(--text-muted);font-size:11px;">Fully local — no data leaves your device</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
