"""
ui/components.py — Shared UI rendering components (Premium v3)
===============================================================
Renders the Top Bar, Hero Section, Feature Grid, and generic UI elements.

v3 improvements:
  - Sticky glassmorphism navbar with animated status indicator
  - Logo with gradient
  - Settings & avatar icon buttons
  - Better empty state design
  - Consistent typography with new font
"""

from __future__ import annotations
import streamlit as st

# ---------------------------------------------------------------------------
# Icons (Lucide SVGs embedded)
# ---------------------------------------------------------------------------
ICONS = {
    "search":    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><path d="m21 21-4.3-4.3"></path></svg>',
    "moon":      '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"></path></svg>',
    "sun":       '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>',
    "settings":  '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"></path><circle cx="12" cy="12" r="3"></circle></svg>',
    "user":      '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="5"></circle><path d="M20 21a8 8 0 0 0-16 0"></path></svg>',
    "bell":      '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>',
    "upload":    '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" x2="12" y1="3" y2="15"></line></svg>',
    "summary":   '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="21" x2="14" y1="4" y2="4"></line><line x1="10" x2="3" y1="4" y2="4"></line><line x1="21" x2="12" y1="12" y2="12"></line><line x1="8" x2="3" y1="12" y2="12"></line><line x1="21" x2="16" y1="20" y2="20"></line><line x1="12" x2="3" y1="20" y2="20"></line><line x1="14" x2="14" y1="2" y2="6"></line><line x1="8" x2="8" y1="10" y2="14"></line><line x1="16" x2="16" y1="18" y2="22"></line></svg>',
    "quiz":      '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" x2="12.01" y1="17" y2="17"></line></svg>',
    "cards":     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"></rect><path d="M3 9h18"></path><path d="M9 21V9"></path></svg>',
    "mindmap":   '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="18" r="3"></circle><circle cx="6" cy="6" r="3"></circle><circle cx="18" cy="6" r="3"></circle><path d="M13 13 8 8"></path><path d="M13 11 15 9"></path><path d="M17 15 15 13"></path></svg>',
    "chat":      '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 9a2 2 0 0 1-2 2H6l-4 4V4c0-1.1.9-2 2-2h8a2 2 0 0 1 2 2v5Z"></path><path d="M18 9h2a2 2 0 0 1 2 2v11l-4-4h-6a2 2 0 0 1-2-2v-1"></path></svg>',
    "keypoints": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" x2="21" y1="6" y2="6"></line><line x1="8" x2="21" y1="12" y2="12"></line><line x1="8" x2="21" y1="18" y2="18"></line><line x1="3" x2="3.01" y1="6" y2="6"></line><line x1="3" x2="3.01" y1="12" y2="12"></line><line x1="3" x2="3.01" y1="18" y2="18"></line></svg>',
    "planner":   '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"></rect><line x1="16" x2="16" y1="2" y2="6"></line><line x1="8" x2="8" y1="2" y2="6"></line><line x1="3" x2="21" y1="10" y2="10"></line><path d="M8 14h.01"></path><path d="M12 14h.01"></path><path d="M16 14h.01"></path><path d="M8 18h.01"></path><path d="M12 18h.01"></path><path d="M16 18h.01"></path></svg>',
}


# ---------------------------------------------------------------------------
# Premium Navbar
# ---------------------------------------------------------------------------

def render_navbar() -> None:
    """Render the Premium Sticky Navigation Bar with glassmorphism."""

    doc_name    = st.session_state.get("file_display_name", "")
    emb_status  = st.session_state.get("embedding_status", "none")
    ai_ready    = emb_status == "ready"
    theme       = st.session_state.get("theme", "dark")

    # Truncate long filenames
    doc_label = doc_name[:32] + "…" if len(doc_name) > 32 else doc_name
    doc_display = f"📄 {doc_label}" if doc_label else "No document loaded"

    # Navbar HTML (non-interactive parts)
    status_color = "#22C55E" if ai_ready else "#64748B"
    status_text  = "AI Ready" if ai_ready else "Waiting for document"
    status_dot_anim = "animation: statusPulse 2s ease-in-out infinite;" if ai_ready else ""

    st.markdown(f"""
    <div style="
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0 14px 0;
        margin-bottom: 20px;
        border-bottom: 1px solid var(--border);
        position: sticky;
        top: 0;
        z-index: 200;
        background: var(--topbar-bg);
        backdrop-filter: blur(20px) saturate(1.5);
        -webkit-backdrop-filter: blur(20px) saturate(1.5);
    ">
        <!-- Logo -->
        <div style="display:flex;align-items:center;gap:10px;">
            <div style="
                width: 34px; height: 34px;
                background: linear-gradient(135deg, var(--primary), var(--accent));
                border-radius: 10px;
                display: flex; align-items: center; justify-content: center;
                font-size: 16px;
                box-shadow: 0 4px 14px rgba(124,92,255,0.4);
            ">⚡</div>
            <div>
                <div style="font-family:var(--font-display);font-size:15px;font-weight:800;
                            background:linear-gradient(135deg,var(--primary),var(--accent));
                            -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                            background-clip:text;letter-spacing:-0.02em;">SmartStudy</div>
                <div style="font-size:10px;color:var(--text-muted);font-weight:500;letter-spacing:0.04em;">AI ASSISTANT</div>
            </div>
        </div>
        <!-- Center: Doc name pill -->
        <div style="
            font-size: 12.5px; font-weight: 500; color: var(--text-secondary);
            background: var(--glass-bg);
            padding: 6px 14px; border-radius: var(--radius-full);
            border: 1px solid var(--glass-border);
            backdrop-filter: blur(8px);
            max-width: 320px;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        ">{doc_display}</div>
        <!-- Right: Status + controls placeholder -->
        <div style="display:flex;align-items:center;gap:10px;">
            <div style="
                display: flex; align-items: center; gap: 6px;
                font-size: 11.5px; font-weight: 600; color: {status_color};
                background: {'rgba(34,197,94,0.08)' if ai_ready else 'rgba(255,255,255,0.04)'};
                padding: 5px 12px; border-radius: var(--radius-full);
                border: 1px solid {'rgba(34,197,94,0.25)' if ai_ready else 'var(--border)'};
            ">
                <span style="width:6px;height:6px;border-radius:50%;background:{status_color};
                             display:inline-block;{status_dot_anim}"></span>
                {status_text}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Theme toggle & settings buttons (functional Streamlit buttons)
    bcol1, bcol2, bcol3 = st.columns([8, 0.6, 0.6])
    with bcol2:
        icon = "☀️" if theme == "dark" else "🌙"
        if st.button(icon, key="theme_toggle_btn", help="Toggle Light/Dark Theme"):
            st.session_state.theme = "light" if theme == "dark" else "dark"
            st.rerun()
    with bcol3:
        if st.button("⚙", key="settings_nav_btn", help="Settings"):
            st.session_state.current_page = "settings"
            st.rerun()


# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------

def render_hero() -> None:
    """Render the hero section."""
    st.markdown("""
    <div class="hero-section">
      <h1 class="text-hero">Your <span class="hero-gradient">AI Study</span> Companion</h1>
      <p class="hero-subtitle">
        Upload PDFs, generate notes, quizzes, flashcards and chat with your documents — all locally.
      </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        btn1, btn2 = st.columns(2)
        with btn1:
            if st.button("Upload Document", type="primary", use_container_width=True, key="hero_upload"):
                st.session_state.current_page = "dashboard"
                st.rerun()
        with btn2:
            if st.button("Start AI Chat", type="secondary", use_container_width=True, key="hero_chat"):
                st.session_state.current_page = "chat"
                st.rerun()


# ---------------------------------------------------------------------------
# Feature Grid
# ---------------------------------------------------------------------------

def render_feature_grid() -> None:
    """Render the Bento feature grid."""
    features = [
        {"icon": ICONS["upload"],    "title": "Upload Documents",  "desc": "Drag and drop PDFs, TXT, or DOCX files safely."},
        {"icon": ICONS["summary"],   "title": "Generate Summary",  "desc": "Condense long readings into accurate summaries."},
        {"icon": ICONS["quiz"],      "title": "Auto Quiz",         "desc": "Test yourself with auto-generated MCQ and short answers."},
        {"icon": ICONS["cards"],     "title": "Flashcards",        "desc": "Memorize key concepts with interactive flip cards."},
        {"icon": ICONS["keypoints"], "title": "Key Points",        "desc": "Extract exactly what matters most from your material."},
        {"icon": ICONS["chat"],      "title": "AI Chat",           "desc": "Chat directly with your document to clarify topics."},
        {"icon": ICONS["mindmap"],   "title": "Mind Map",          "desc": "Visualize connections between concepts visually."},
        {"icon": ICONS["planner"],   "title": "Study Planner",     "desc": "Organize your reading flow efficiently."},
    ]

    html = '<div class="bento-grid">'
    for f in features:
        html += f"""
        <div class="bento-card">
          <div class="bento-icon">{f['icon']}</div>
          <div class="text-card-title">{f['title']}</div>
          <div class="text-body">{f['desc']}</div>
        </div>
        """
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def render_time_badge(t: float, category: str) -> None:
    """Render a subtle timing badge."""
    st.markdown(
        f'<div style="text-align:right;"><span style="font-size:11px;color:var(--text-muted);">⏱ {t:.1f}s</span></div>',
        unsafe_allow_html=True,
    )


def section_label(icon: str, title: str) -> None:
    """Render a clean section title."""
    st.markdown(
        f'<div style="margin:24px 0 16px;font-family:var(--font-display);font-size:22px;font-weight:700;color:var(--text-primary);">{icon} {title}</div>',
        unsafe_allow_html=True,
    )


def render_empty_state(icon: str, title: str, desc: str) -> None:
    """Render a premium empty state card."""
    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 56px 32px;
        border: 1px dashed var(--border);
        border-radius: var(--radius-xl);
        margin-top: 24px;
        background: var(--glass-bg);
        backdrop-filter: blur(10px);
        animation: fadeInScale 0.4s ease;
    ">
        <div style="font-size:36px;margin-bottom:16px;">{icon}</div>
        <div style="font-size:18px;font-weight:700;color:var(--text-primary);margin-bottom:8px;">{title}</div>
        <div style="font-size:13.5px;color:var(--text-secondary);max-width:320px;margin:0 auto;line-height:1.65;">{desc}</div>
    </div>
    """, unsafe_allow_html=True)


def render_typing_indicator() -> None:
    """Render a clean animated typing indicator."""
    st.markdown("""
    <div style="display:flex;gap:5px;padding:12px 16px;background:var(--glass-bg);
                border-radius:var(--radius-lg);width:fit-content;border:1px solid var(--glass-border);
                backdrop-filter:blur(10px);">
        <div style="width:7px;height:7px;border-radius:50%;background:var(--primary);
                    animation:dotPulse 1.3s ease-in-out infinite;animation-delay:0s;"></div>
        <div style="width:7px;height:7px;border-radius:50%;background:var(--primary);
                    animation:dotPulse 1.3s ease-in-out infinite;animation-delay:0.2s;"></div>
        <div style="width:7px;height:7px;border-radius:50%;background:var(--primary);
                    animation:dotPulse 1.3s ease-in-out infinite;animation-delay:0.4s;"></div>
    </div>
    """, unsafe_allow_html=True)
