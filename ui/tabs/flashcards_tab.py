"""
ui/tabs/flashcards_tab.py — Interactive Flip Flashcard Deck (v3)
=================================================================
Parses LLM's flashcard output into Q/A pairs and renders
a full interactive flip-card deck with:
  - 3D CSS flip animation (front=Question, back=Answer)
  - Previous / Next / Shuffle navigation
  - Progress counter with animated bar
  - All-cards summary collapsible

v3: CSS aligned with styles.py v3 (glass-card, quiz-score-bar/fill, card-section-label)
"""

from __future__ import annotations
import re
import random

import streamlit as st
from ui.components import render_empty_state, render_time_badge


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def _parse_flashcards(raw) -> list[dict[str, str]]:
    """Parse flashcard data into a list of {q, a} dicts."""
    if isinstance(raw, list):
        cards = []
        for item in raw:
            q = item.get("front", "").strip()
            a = item.get("back", "").strip()
            if q and a:
                cards.append({"q": q, "a": a})
        return cards[:15]

    raw = str(raw)
    cards = []
    # Split by "Card N:"
    blocks = re.split(r"Card\s+\d+\s*:", raw, flags=re.IGNORECASE)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        q_match = re.search(r"Q\s*:\s*(.+?)(?=A\s*:|$)", block, re.IGNORECASE | re.DOTALL)
        a_match = re.search(r"A\s*:\s*(.+?)$", block, re.IGNORECASE | re.DOTALL)
        if q_match and a_match:
            q = q_match.group(1).strip().replace("\n", " ")
            a = a_match.group(1).strip().replace("\n", " ")
            if q and a:
                cards.append({"q": q, "a": a})

    if not cards:
        lines = [l.strip() for l in raw.split("\n") if l.strip()]
        i = 0
        while i < len(lines) - 1:
            if re.match(r"^Q\s*:", lines[i], re.IGNORECASE):
                q_text = re.sub(r"^Q\s*:\s*", "", lines[i], flags=re.IGNORECASE)
                a_text = ""
                if i + 1 < len(lines) and re.match(r"^A\s*:", lines[i+1], re.IGNORECASE):
                    a_text = re.sub(r"^A\s*:\s*", "", lines[i+1], flags=re.IGNORECASE)
                    i += 2
                else:
                    i += 1
                if q_text and a_text:
                    cards.append({"q": q_text, "a": a_text})
            else:
                i += 1

    return cards[:15]


# ---------------------------------------------------------------------------
# Session state helpers
# ---------------------------------------------------------------------------

def _init_flashcard_state(cards: list[dict]) -> None:
    n = len(cards)
    if "fc_idx" not in st.session_state:
        st.session_state.fc_idx = 0
    if "fc_order" not in st.session_state or len(st.session_state.fc_order) != n:
        st.session_state.fc_order = list(range(n))
    if st.session_state.fc_idx >= n:
        st.session_state.fc_idx = 0


# ---------------------------------------------------------------------------
# Flip card HTML
# ---------------------------------------------------------------------------

_FLIP_CARD_HTML = """
<!DOCTYPE html>
<html>
<head>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: transparent; font-family: 'Inter', 'Plus Jakarta Sans', sans-serif; }}

  .fc-scene {{
    width: 100%;
    min-height: 210px;
    perspective: 1000px;
    cursor: pointer;
    user-select: none;
  }}
  .fc-card {{
    width: 100%;
    min-height: 210px;
    position: relative;
    transform-style: preserve-3d;
    transition: transform 0.55s cubic-bezier(0.4,0,0.2,1);
    border-radius: 18px;
  }}
  .fc-card.flipped {{
    transform: rotateY(180deg);
  }}
  .fc-face {{
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    backface-visibility: hidden;
    -webkit-backface-visibility: hidden;
    border-radius: 18px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem 2.5rem;
    text-align: center;
    min-height: 210px;
  }}
  .fc-front {{
    background: linear-gradient(135deg, #1a2040 0%, #0F172A 100%);
    border: 1px solid rgba(99,102,241,0.28);
    box-shadow: 0 0 30px rgba(99,102,241,0.12), 0 8px 40px rgba(0,0,0,0.45);
  }}
  .fc-back {{
    background: linear-gradient(135deg, #1a1548 0%, #0F172A 100%);
    border: 1px solid rgba(139,92,246,0.28);
    box-shadow: 0 0 30px rgba(139,92,246,0.12), 0 8px 40px rgba(0,0,0,0.45);
    transform: rotateY(180deg);
  }}
  .fc-side-label {{
    font-size: 0.6rem;
    font-weight: 800;
    letter-spacing: 0.13em;
    text-transform: uppercase;
    margin-bottom: 0.9rem;
    padding: 0.25rem 0.8rem;
    border-radius: 999px;
  }}
  .fc-front .fc-side-label {{
    background: rgba(99,102,241,0.14);
    border: 1px solid rgba(99,102,241,0.28);
    color: #818CF8;
  }}
  .fc-back .fc-side-label {{
    background: rgba(139,92,246,0.14);
    border: 1px solid rgba(139,92,246,0.28);
    color: #C4B5FD;
  }}
  .fc-text {{
    font-size: 1rem;
    font-weight: 600;
    color: #F1F5F9;
    line-height: 1.65;
    max-width: 88%;
  }}
  .fc-back .fc-text {{
    font-size: 0.9rem;
    font-weight: 500;
    color: #CBD5E1;
  }}
  .fc-hint {{
    position: absolute;
    bottom: 1rem;
    font-size: 0.65rem;
    color: rgba(255,255,255,0.22);
    letter-spacing: 0.04em;
  }}
  .fc-icon {{
    font-size: 1.8rem;
    margin-bottom: 0.75rem;
    opacity: 0.9;
  }}
</style>
</head>
<body>
  <div class="fc-scene" onclick="document.querySelector('.fc-card').classList.toggle('flipped')">
    <div class="fc-card" id="card">
      <div class="fc-face fc-front">
        <span class="fc-side-label">❓ Question</span>
        <div class="fc-icon">🧠</div>
        <div class="fc-text">{question}</div>
        <div class="fc-hint">👆 Click to reveal answer</div>
      </div>
      <div class="fc-face fc-back">
        <span class="fc-side-label">✅ Answer</span>
        <div class="fc-icon">💡</div>
        <div class="fc-text">{answer}</div>
        <div class="fc-hint">👆 Click to flip back</div>
      </div>
    </div>
  </div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Main renderer
# ---------------------------------------------------------------------------

def render_flashcards_tab(study_output: dict | None) -> None:
    """Render the interactive flip-card flashcard deck."""
    if not study_output:
        render_empty_state(
            "🃏",
            "No Flashcards Yet",
            "Generate study notes to create your interactive flashcard deck.",
        )
        return

    raw   = study_output.get("flashcards", "")
    cards = _parse_flashcards(raw)
    proc_times = st.session_state.get("processing_times", {})
    t = proc_times.get("Flashcards", proc_times.get("Study Material", None))

    # ── Header ───────────────────────────────────────────────────────────────
    h_col, t_col = st.columns([3, 1])
    with h_col:
        st.markdown(
            '<div class="card-section-label">🃏 Spaced-Repetition Flashcards</div>',
            unsafe_allow_html=True,
        )
    with t_col:
        if t:
            render_time_badge(t, "flashcards")

    if not cards:
        st.markdown(raw)
        return

    _init_flashcard_state(cards)

    total = len(cards)
    order = st.session_state.fc_order
    idx   = st.session_state.fc_idx
    c_idx = order[idx]
    card  = cards[c_idx]

    # ── Progress bar ──────────────────────────────────────────────────────────
    progress = (idx + 1) / total
    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
      <div style="font-size:13px;font-weight:700;color:var(--text-primary);">
        Card <span style="color:var(--primary);">{idx + 1}</span> of {total}
      </div>
      <div style="font-size:11px;color:var(--text-muted);">{round(progress * 100)}% completed</div>
    </div>
    <div class="quiz-score-bar" style="margin-bottom:18px;">
      <div class="quiz-score-fill" style="width:{progress*100:.1f}%;"></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Flip card ─────────────────────────────────────────────────────────────
    html_content = _FLIP_CARD_HTML.format(
        question=card["q"].replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;"),
        answer=card["a"].replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;"),
    )
    st.components.v1.html(html_content, height=240, scrolling=False)

    # ── Navigation buttons ────────────────────────────────────────────────────
    st.markdown('<div style="margin-top:16px;"></div>', unsafe_allow_html=True)
    nav1, nav2, nav3, nav4 = st.columns(4)

    with nav1:
        if st.button("◀ Prev", key="fc_prev", use_container_width=True):
            st.session_state.fc_idx = (idx - 1) % total
            st.rerun()
    with nav2:
        if st.button("Next ▶", key="fc_next", use_container_width=True):
            st.session_state.fc_idx = (idx + 1) % total
            st.rerun()
    with nav3:
        if st.button("🔀 Shuffle", key="fc_shuffle", use_container_width=True):
            new_order = list(range(total))
            random.shuffle(new_order)
            st.session_state.fc_order = new_order
            st.session_state.fc_idx   = 0
            st.rerun()
    with nav4:
        if st.button("↩ Reset", key="fc_reset", use_container_width=True):
            st.session_state.fc_order = list(range(total))
            st.session_state.fc_idx   = 0
            st.rerun()

    # ── All cards summary (collapsed) ─────────────────────────────────────────
    with st.expander(f"📋 View All {total} Flashcards", expanded=False):
        for i, c in enumerate(cards):
            st.markdown(f"""
            <div class="glass-card" style="padding:14px;margin-bottom:8px;">
              <div style="font-size:10.5px;font-weight:700;color:var(--primary);
                          text-transform:uppercase;letter-spacing:0.1em;margin-bottom:5px;">
                Card {i+1}
              </div>
              <div style="font-size:13.5px;font-weight:600;color:var(--text-primary);margin-bottom:5px;">
                Q: {c["q"]}
              </div>
              <div style="font-size:12.5px;color:var(--text-secondary);line-height:1.55;">
                A: {c["a"]}
              </div>
            </div>
            """, unsafe_allow_html=True)
