"""
ui/styles.py — Master CSS for Smart Study Assistant (Premium Edition)
======================================================================
Single source of truth for ALL custom CSS.
Inject via:   st.markdown(get_css(), unsafe_allow_html=True)

Changelog v3:
  - Added ALL missing CSS classes referenced by tab components
  - Complete light/dark theme dual-support
  - Glassmorphism on sidebar, cards, inputs, buttons
  - Chat bubbles, source cards, quiz score bar
  - Key-point cards (kp-card, kp-number, kp-text)
  - Skeleton loaders + success animation
  - Ripple effect on buttons
  - Smooth micro-animations everywhere
"""

from __future__ import annotations

import streamlit as st

def get_css() -> str:
    theme = st.session_state.get('theme', 'dark')

    if theme == 'light':
        colors = """
  --bg-primary:       #F0F4FF;
  --bg-secondary:     #E8EEFF;
  --bg-card:          rgba(255, 255, 255, 0.85);
  --bg-card-solid:    #FFFFFF;
  --border:           rgba(99, 102, 241, 0.15);
  --border-soft:      rgba(0, 0, 0, 0.07);
  --primary:          #6366F1;
  --primary-hover:    #4F46E5;
  --accent:           #0EA5E9;
  --success:          #10B981;
  --warning:          #F59E0B;
  --danger:           #EF4444;
  --text-primary:     #0F172A;
  --text-secondary:   #475569;
  --text-muted:       #94A3B8;
  --shadow-sm:        0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06);
  --shadow-md:        0 4px 16px rgba(0,0,0,0.10), 0 2px 6px rgba(0,0,0,0.06);
  --shadow-lg:        0 10px 40px rgba(0,0,0,0.12);
  --shadow-glow:      0 0 24px rgba(99, 102, 241, 0.25);
  --glass-bg:         rgba(255, 255, 255, 0.7);
  --glass-border:     rgba(99, 102, 241, 0.2);
  --sidebar-bg:       rgba(240, 244, 255, 0.95);
  --topbar-bg:        rgba(240, 244, 255, 0.90);
  --user-bubble:      rgba(99, 102, 241, 0.12);
  --ai-bubble:        rgba(255, 255, 255, 0.95);
"""
    else:
        colors = """
  --bg-primary:       #080E1A;
  --bg-secondary:     #0D1526;
  --bg-card:          rgba(20, 27, 48, 0.80);
  --bg-card-solid:    #141B30;
  --border:           rgba(255, 255, 255, 0.08);
  --border-soft:      rgba(255, 255, 255, 0.05);
  --primary:          #7C5CFF;
  --primary-hover:    #9D84FF;
  --accent:           #00C2FF;
  --success:          #22C55E;
  --warning:          #F59E0B;
  --danger:           #EF4444;
  --text-primary:     #F1F5F9;
  --text-secondary:   #94A3B8;
  --text-muted:       #64748B;
  --shadow-sm:        0 1px 3px rgba(0,0,0,0.3);
  --shadow-md:        0 4px 16px rgba(0,0,0,0.4);
  --shadow-lg:        0 10px 40px rgba(0,0,0,0.5);
  --shadow-glow:      0 0 32px rgba(124, 92, 255, 0.20);
  --glass-bg:         rgba(14, 21, 38, 0.70);
  --glass-border:     rgba(255, 255, 255, 0.09);
  --sidebar-bg:       rgba(8, 14, 26, 0.90);
  --topbar-bg:        rgba(8, 14, 26, 0.85);
  --user-bubble:      rgba(124, 92, 255, 0.18);
  --ai-bubble:        rgba(20, 27, 48, 0.95);
"""

    return f"""
<style>
/* ===========================================================
   SECTION 0 — GOOGLE FONTS
   =========================================================== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

/* ===========================================================
   SECTION 1 — CSS CUSTOM PROPERTIES
   =========================================================== */
:root {{
{colors}

  /* Spacing (8-pt grid) */
  --sp-1:  8px;
  --sp-2:  16px;
  --sp-3:  24px;
  --sp-4:  32px;
  --sp-5:  40px;
  --sp-6:  48px;

  /* Border radii */
  --radius-xs:   6px;
  --radius-sm:   8px;
  --radius-md:   12px;
  --radius-lg:   16px;
  --radius-xl:   20px;
  --radius-2xl:  24px;
  --radius-full: 9999px;

  /* Typography */
  --font-sans:    'Inter', 'Plus Jakarta Sans', system-ui, sans-serif;
  --font-display: 'Plus Jakarta Sans', 'Inter', system-ui, sans-serif;

  /* Transitions */
  --ease:       cubic-bezier(0.16, 1, 0.3, 1);
  --transition: all 0.22s var(--ease);
  --transition-slow: all 0.4s var(--ease);
}}

/* ===========================================================
   SECTION 2 — GLOBAL RESETS
   =========================================================== */
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"] {{
  background: var(--bg-primary) !important;
  font-family: var(--font-sans) !important;
  color: var(--text-primary) !important;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}}

[data-testid="block-container"] {{
  max-width: 1360px !important;
  padding: 0 var(--sp-4) var(--sp-6) var(--sp-4) !important;
}}

[data-testid="stAppViewContainer"] > .main > div {{
  padding-top: 0 !important;
}}

/* Hide Streamlit chrome */
#MainMenu, footer, header {{ visibility: hidden !important; }}
[data-testid="stToolbar"] {{ display: none !important; }}
[data-testid="stDecoration"] {{ display: none !important; }}

/* ===========================================================
   SECTION 3 — TYPOGRAPHY
   =========================================================== */
h1, h2, h3, h4, h5, h6 {{
  font-family: var(--font-display) !important;
  color: var(--text-primary) !important;
  letter-spacing: -0.025em;
}}

.text-hero {{
  font-size: clamp(40px, 6vw, 60px);
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -0.035em;
}}
.text-section {{
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--text-primary);
}}
.text-card-title {{
  font-size: 17px;
  font-weight: 700;
  color: var(--text-primary);
}}
.text-body {{
  font-size: 14px;
  line-height: 1.65;
  color: var(--text-secondary);
}}
.card-section-label {{
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--primary);
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 6px;
}}
.hero-gradient {{
  background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}}
.stMarkdown p {{
  color: var(--text-secondary) !important;
  font-size: 14.5px;
  line-height: 1.65;
}}
code, pre {{
  font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace !important;
}}

/* ===========================================================
   SECTION 4 — SIDEBAR
   =========================================================== */
section[data-testid="stSidebar"] {{
  background: var(--sidebar-bg) !important;
  border-right: 1px solid var(--glass-border) !important;
  backdrop-filter: blur(20px) saturate(1.4) !important;
  -webkit-backdrop-filter: blur(20px) saturate(1.4) !important;
}}
section[data-testid="stSidebar"] > div {{
  background: transparent !important;
}}
.sidebar-divider {{
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--border), transparent);
  margin: var(--sp-2) 0;
}}

/* ===========================================================
   SECTION 5 — PREMIUM NAVBAR / TOPBAR
   =========================================================== */
.topbar {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: var(--topbar-bg);
  backdrop-filter: blur(20px) saturate(1.5);
  -webkit-backdrop-filter: blur(20px) saturate(1.5);
  border-bottom: 1px solid var(--glass-border);
  position: sticky;
  top: 0;
  z-index: 200;
  margin: 0 calc(-1 * var(--sp-4)) var(--sp-4);
}}
.topbar-right {{
  display: flex;
  gap: var(--sp-2);
  align-items: center;
}}
.topbar-badge {{
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  background: rgba(34, 197, 94, 0.1);
  color: var(--success);
  border-radius: var(--radius-full);
  border: 1px solid rgba(34, 197, 94, 0.25);
  display: flex;
  align-items: center;
  gap: 5px;
}}
.topbar-badge::before {{
  content: '';
  width: 5px; height: 5px;
  border-radius: 50%;
  background: var(--success);
  display: inline-block;
  animation: statusPulse 2s ease-in-out infinite;
}}
@keyframes statusPulse {{
  0%, 100% {{ opacity: 1; transform: scale(1); }}
  50%        {{ opacity: 0.5; transform: scale(0.8); }}
}}

/* ===========================================================
   SECTION 6 — GLASSMORPHISM CARDS
   =========================================================== */
.glass-card {{
  background: var(--glass-bg) !important;
  backdrop-filter: blur(16px) saturate(1.3) !important;
  -webkit-backdrop-filter: blur(16px) saturate(1.3) !important;
  border: 1px solid var(--glass-border) !important;
  border-radius: var(--radius-xl) !important;
  padding: var(--sp-3) !important;
  transition: var(--transition) !important;
  box-shadow: var(--shadow-md) !important;
}}
.glass-card:hover {{
  border-color: rgba(124, 92, 255, 0.25) !important;
  box-shadow: var(--shadow-lg), var(--shadow-glow) !important;
  transform: translateY(-2px);
}}
.glass-card-accent {{
  border-color: rgba(124, 92, 255, 0.2) !important;
  background: linear-gradient(
    135deg,
    rgba(124, 92, 255, 0.06) 0%,
    var(--glass-bg) 100%
  ) !important;
}}

/* Bento grid */
.bento-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: var(--sp-3);
  margin: var(--sp-4) 0;
}}
.bento-card {{
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--sp-3);
  transition: var(--transition);
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow: var(--shadow-sm);
}}
.bento-card:hover {{
  border-color: rgba(124, 92, 255, 0.3);
  box-shadow: var(--shadow-md), var(--shadow-glow);
  transform: translateY(-3px);
}}
.bento-icon {{
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, rgba(124, 92, 255, 0.15), rgba(0, 194, 255, 0.08));
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-primary);
  flex-shrink: 0;
}}

/* Status chips */
.status-chip {{
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border-radius: var(--radius-full);
  font-size: 11px;
  font-weight: 600;
  border: 1px solid var(--border);
}}
.status-ready   {{ background: rgba(34, 197, 94, 0.10); color: var(--success); border-color: rgba(34, 197, 94, 0.25); }}
.status-building{{ background: rgba(0, 194, 255, 0.10); color: var(--accent);  border-color: rgba(0, 194, 255, 0.25); }}
.status-none    {{ background: rgba(255,255,255,0.04); color: var(--text-muted); }}

.dot            {{ width: 6px; height: 6px; border-radius: 50%; display: inline-block; flex-shrink:0; }}
.dot-green      {{ background: var(--success); box-shadow: 0 0 6px var(--success); }}
.dot-yellow     {{ background: var(--warning); box-shadow: 0 0 6px var(--warning); }}
.dot-gray       {{ background: var(--text-muted); }}

/* ===========================================================
   SECTION 7 — PREMIUM BUTTONS
   =========================================================== */
.stButton > button {{
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  color: var(--text-primary) !important;
  backdrop-filter: blur(12px) !important;
  -webkit-backdrop-filter: blur(12px) !important;
  border-radius: var(--radius-md) !important;
  box-shadow: var(--shadow-sm) !important;
  font-family: var(--font-sans) !important;
  font-weight: 600 !important;
  font-size: 14px !important;
  transition: var(--transition) !important;
  position: relative !important;
  overflow: hidden !important;
  padding: 8px 18px !important;
}}
.stButton > button::after {{
  content: '' !important;
  position: absolute !important;
  inset: 0 !important;
  background: radial-gradient(circle, rgba(255,255,255,0.25) 0%, transparent 65%) !important;
  opacity: 0 !important;
  transition: opacity 0.3s !important;
  border-radius: inherit !important;
}}
.stButton > button:hover {{
  transform: translateY(-2px) scale(1.015) !important;
  box-shadow: var(--shadow-md), var(--shadow-glow) !important;
  border-color: var(--primary) !important;
}}
.stButton > button:hover::after {{
  opacity: 1 !important;
}}
.stButton > button:active {{
  transform: translateY(0px) scale(0.97) !important;
  box-shadow: var(--shadow-sm) !important;
}}
.stButton > button:disabled {{
  opacity: 0.45 !important;
  cursor: not-allowed !important;
  transform: none !important;
  box-shadow: none !important;
}}

/* Primary CTA buttons */
.stButton > button[kind="primary"],
button[data-testid="baseButton-primary"] {{
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%) !important;
  border: none !important;
  color: #ffffff !important;
  box-shadow: 0 4px 16px rgba(124,92,255,0.30) !important;
}}
.stButton > button[kind="primary"]:hover,
button[data-testid="baseButton-primary"]:hover {{
  box-shadow: 0 6px 24px rgba(124,92,255,0.45) !important;
  transform: translateY(-2px) scale(1.015) !important;
}}

/* Secondary buttons */
button[data-testid="baseButton-secondary"] {{
  background: transparent !important;
  color: var(--text-primary) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-md) !important;
  font-family: var(--font-sans) !important;
  font-size: 14px !important;
  font-weight: 600 !important;
  transition: var(--transition) !important;
}}
button[data-testid="baseButton-secondary"]:hover {{
  background: rgba(124,92,255,0.08) !important;
  border-color: var(--primary) !important;
}}

/* Download button */
.stDownloadButton > button {{
  background: var(--bg-card) !important;
  color: var(--text-secondary) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-md) !important;
  font-family: var(--font-sans) !important;
  font-weight: 600 !important;
  font-size: 13px !important;
  transition: var(--transition) !important;
}}
.stDownloadButton > button:hover {{
  border-color: var(--primary) !important;
  color: var(--text-primary) !important;
  box-shadow: var(--shadow-glow) !important;
}}

/* ===========================================================
   SECTION 8 — INPUTS (GLASSMORPHISM)
   =========================================================== */
[data-testid="stTextArea"] textarea,
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] > div > div {{
  background: var(--glass-bg) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  color: var(--text-primary) !important;
  font-family: var(--font-sans) !important;
  font-size: 14px !important;
  transition: var(--transition) !important;
  backdrop-filter: blur(8px) !important;
}}
[data-testid="stTextArea"] textarea:focus,
[data-testid="stTextInput"] input:focus {{
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 2px rgba(124, 92, 255, 0.18) !important;
  outline: none !important;
}}

/* Radio buttons */
[data-testid="stRadio"] > div {{
  gap: 8px;
}}
[data-testid="stRadio"] label {{
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  padding: 8px 14px !important;
  transition: var(--transition) !important;
  cursor: pointer;
}}
[data-testid="stRadio"] label:hover {{
  border-color: var(--primary) !important;
  background: rgba(124,92,255,0.06) !important;
}}

/* ===========================================================
   SECTION 9 — UPLOAD SECTION
   =========================================================== */
[data-testid="stFileUploader"] {{
  background: var(--bg-card) !important;
  border: 2px dashed var(--border) !important;
  border-radius: var(--radius-xl) !important;
  padding: var(--sp-5) !important;
  transition: var(--transition) !important;
  backdrop-filter: blur(8px) !important;
}}
[data-testid="stFileUploader"]:hover {{
  border-color: var(--primary) !important;
  background: rgba(124, 92, 255, 0.04) !important;
  box-shadow: var(--shadow-glow) !important;
}}
[data-testid="stFileUploader"] section {{
  text-align: center;
}}

/* ===========================================================
   SECTION 10 — STREAMLIT TABS
   =========================================================== */
[data-testid="stTabs"] {{ background: transparent; }}
[data-testid="stTabs"] [role="tablist"] {{
  background: transparent !important;
  border: none !important;
  border-bottom: 1px solid var(--border) !important;
  border-radius: 0 !important;
  padding: 0 !important;
  gap: var(--sp-3) !important;
}}
[data-testid="stTabs"] [role="tab"] {{
  background: transparent !important;
  color: var(--text-muted) !important;
  border: none !important;
  border-radius: 0 !important;
  font-family: var(--font-sans) !important;
  font-weight: 500 !important;
  font-size: 14px !important;
  padding: var(--sp-2) 0 !important;
  margin: 0 !important;
  border-bottom: 2px solid transparent !important;
  transition: var(--transition) !important;
}}
[data-testid="stTabs"] [role="tab"]:hover {{
  color: var(--text-primary) !important;
  background: transparent !important;
}}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
  color: var(--text-primary) !important;
  border-bottom: 2px solid var(--primary) !important;
  box-shadow: none !important;
  font-weight: 700 !important;
}}
[data-testid="stTabs"] [role="tabpanel"] {{
  padding-top: var(--sp-4) !important;
  background: transparent !important;
  border: none !important;
}}

/* ===========================================================
   SECTION 11 — METRICS & ALERTS
   =========================================================== */
[data-testid="stMetric"] {{
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-lg) !important;
  padding: var(--sp-2) !important;
  backdrop-filter: blur(10px) !important;
  transition: var(--transition) !important;
}}
[data-testid="stMetric"]:hover {{
  border-color: var(--primary) !important;
  transform: translateY(-2px);
}}
[data-testid="stMetricValue"] {{
  font-family: var(--font-display) !important;
  font-weight: 800 !important;
  color: var(--text-primary) !important;
}}

[data-testid="stSuccess"],
[data-testid="stError"],
[data-testid="stWarning"],
[data-testid="stInfo"] {{
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-md) !important;
  padding: var(--sp-2) !important;
}}

/* ===========================================================
   SECTION 12 — KEY POINTS CARDS
   =========================================================== */
@keyframes kpSlideIn {{
  from {{ opacity: 0; transform: translateX(-20px); }}
  to   {{ opacity: 1; transform: translateX(0); }}
}}

.kp-card {{
  display: flex;
  align-items: flex-start;
  gap: 16px;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  padding: 18px 22px;
  margin-bottom: 12px;
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  box-shadow: var(--shadow-sm);
  animation: kpSlideIn 0.4s var(--ease) both;
  transition: var(--transition);
}}
.kp-card:hover {{
  border-color: rgba(124, 92, 255, 0.3);
  box-shadow: var(--shadow-md), var(--shadow-glow);
  transform: translateX(4px);
}}
.kp-number {{
  min-width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  background: linear-gradient(135deg, var(--primary), var(--primary-hover));
  color: #fff;
  font-size: 13px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(124,92,255,0.35);
}}
.kp-text {{
  font-size: 14.5px;
  font-weight: 500;
  color: var(--text-primary);
  line-height: 1.65;
}}

/* ===========================================================
   SECTION 13 — QUIZ PROGRESS & SCORE BAR
   =========================================================== */
.quiz-score-bar {{
  background: var(--border);
  border-radius: var(--radius-full);
  height: 5px;
  overflow: hidden;
  margin-bottom: 4px;
}}
.quiz-score-fill {{
  height: 100%;
  background: linear-gradient(90deg, var(--primary), var(--accent));
  border-radius: var(--radius-full);
  transition: width 0.6s var(--ease);
}}

/* ===========================================================
   SECTION 14 — CHAT UI
   =========================================================== */
.chat-container {{
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 12px 0;
  max-height: 68vh;
  overflow-y: auto;
  scroll-behavior: smooth;
}}
.chat-container::-webkit-scrollbar {{
  width: 4px;
}}
.chat-container::-webkit-scrollbar-track {{
  background: transparent;
}}
.chat-container::-webkit-scrollbar-thumb {{
  background: var(--border);
  border-radius: var(--radius-full);
}}

/* Message rows */
.chat-message {{
  display: flex;
  align-items: flex-start;
  gap: 12px;
  animation: chatFadeIn 0.35s var(--ease) both;
}}
.chat-message.user {{
  flex-direction: row-reverse;
}}
@keyframes chatFadeIn {{
  from {{ opacity: 0; transform: translateY(10px); }}
  to   {{ opacity: 1; transform: translateY(0); }}
}}

/* Avatars */
.chat-avatar {{
  width: 34px;
  height: 34px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  flex-shrink: 0;
  border: 1px solid var(--border);
}}
.avatar-ai {{
  background: linear-gradient(135deg, var(--primary), var(--accent));
  border: none;
}}
.avatar-user {{
  background: var(--user-bubble);
  border-color: rgba(124,92,255,0.25);
}}

/* Bubbles */
.chat-bubble {{
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14.5px;
  line-height: 1.65;
  max-width: 78%;
  word-break: break-word;
  box-shadow: var(--shadow-sm);
}}
.bubble-user {{
  background: var(--user-bubble);
  border: 1px solid rgba(124,92,255,0.22);
  border-radius: 16px 4px 16px 16px;
  color: var(--text-primary);
  align-self: flex-end;
}}
.bubble-ai {{
  background: var(--ai-bubble);
  border: 1px solid var(--glass-border);
  border-radius: 4px 16px 16px 16px;
  color: var(--text-primary);
  backdrop-filter: blur(10px);
}}

/* Chat meta (timestamp) */
.chat-meta {{
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
  padding: 0 4px;
}}
.chat-timestamp {{
  font-size: 10px;
  color: var(--text-muted);
  font-weight: 500;
}}

/* Source cards */
.source-card {{
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-md);
  padding: 12px 14px;
  margin-bottom: 8px;
  backdrop-filter: blur(8px);
  transition: var(--transition);
}}
.source-card:hover {{
  border-color: rgba(124,92,255,0.25);
}}
.source-card-header {{
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}}
.source-badge {{
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  background: rgba(124,92,255,0.15);
  color: var(--primary-hover);
  border: 1px solid rgba(124,92,255,0.25);
}}

/* ===========================================================
   SECTION 15 — SKELETON LOADERS
   =========================================================== */
@keyframes skeletonShimmer {{
  0%   {{ background-position: -400px 0; }}
  100% {{ background-position:  400px 0; }}
}}
.skeleton-box {{
  background: linear-gradient(
    90deg,
    var(--bg-card) 25%,
    rgba(255,255,255,0.06) 50%,
    var(--bg-card) 75%
  );
  background-size: 800px 100%;
  animation: skeletonShimmer 1.8s infinite linear;
  border-radius: var(--radius-sm);
  height: 18px;
  margin-bottom: 10px;
}}
.skeleton-title  {{ height: 26px; width: 42%; margin-bottom: 22px; }}
.skeleton-text-full  {{ width: 100%; }}
.skeleton-text-lg    {{ width: 82%; }}
.skeleton-text-md    {{ width: 60%; }}
.skeleton-text-sm    {{ width: 38%; }}
.skeleton-card   {{ height: 110px; border-radius: var(--radius-md); }}

/* ===========================================================
   SECTION 16 — HERO SECTION
   =========================================================== */
.hero-section {{
  text-align: center;
  padding: var(--sp-6) 0 var(--sp-4);
  position: relative;
}}
.hero-subtitle {{
  font-size: 17px;
  color: var(--text-secondary);
  max-width: 580px;
  margin: var(--sp-3) auto var(--sp-4);
  line-height: 1.65;
}}
.hero-buttons {{
  display: flex;
  gap: var(--sp-2);
  justify-content: center;
}}

/* ===========================================================
   SECTION 17 — PROGRESS / ANIMATIONS
   =========================================================== */
@keyframes fadeInUp {{
  from {{ opacity: 0; transform: translateY(16px); }}
  to   {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes fadeInScale {{
  from {{ opacity: 0; transform: scale(0.92); }}
  to   {{ opacity: 1; transform: scale(1); }}
}}
@keyframes successBounce {{
  0%   {{ transform: scale(0.8); opacity: 0; }}
  60%  {{ transform: scale(1.12); opacity: 1; }}
  100% {{ transform: scale(1); opacity: 1; }}
}}
@keyframes dotPulse {{
  0%, 80%, 100% {{ opacity: 0.2; transform: scale(0.75); }}
  40%           {{ opacity: 1;   transform: scale(1.15); }}
}}
.dot-pulse {{
  width: 7px; height: 7px;
  border-radius: 50%;
  background: var(--primary);
  display: inline-block;
  animation: dotPulse 1.3s ease-in-out infinite;
}}

/* Progress bar (Streamlit native override) */
.stProgress > div > div > div > div {{
  background: linear-gradient(90deg, var(--primary), var(--accent)) !important;
  border-radius: var(--radius-full) !important;
}}
.stProgress > div > div > div {{
  background: var(--border) !important;
  border-radius: var(--radius-full) !important;
}}

/* ===========================================================
   SECTION 18 — SUMMARY CONTENT
   =========================================================== */
.summary-content {{
  font-size: 15px;
  line-height: 1.8;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
}}

/* ===========================================================
   SECTION 19 — EXPANDER
   =========================================================== */
[data-testid="stExpander"] {{
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-lg) !important;
  backdrop-filter: blur(10px) !important;
}}
[data-testid="stExpander"] summary {{
  font-weight: 600 !important;
  color: var(--text-primary) !important;
}}

/* ===========================================================
   SECTION 20 — SPINNER OVERRIDE
   =========================================================== */
[data-testid="stSpinner"] > div {{
  border-top-color: var(--primary) !important;
}}

/* ===========================================================
   SECTION 21 — SCROLLBAR (GLOBAL)
   =========================================================== */
* {{
  scrollbar-width: thin;
  scrollbar-color: var(--border) transparent;
}}
*::-webkit-scrollbar {{ width: 5px; height: 5px; }}
*::-webkit-scrollbar-track {{ background: transparent; }}
*::-webkit-scrollbar-thumb {{
  background: var(--border);
  border-radius: var(--radius-full);
}}
*::-webkit-scrollbar-thumb:hover {{
  background: var(--text-muted);
}}
</style>
"""
