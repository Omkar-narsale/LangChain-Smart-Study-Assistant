"""
ui/tabs/keypoints_tab.py — Premium Key Points Cards (v3)
=========================================================
Each key point is rendered inside its own animated glass card.
Parses numbered list from LLM output.

v3: CSS class names aligned with styles.py v3 (kp-card, kp-number, kp-text)
"""

from __future__ import annotations
import re

import streamlit as st
from ui.components import render_empty_state, render_time_badge


_ICONS = ["💡", "🎯", "📌", "🔑", "⚙️", "📐", "🧩", "🌟", "🔬", "📊"]


def _parse_key_points(raw: str) -> list[str]:
    """Extract individual key points from the numbered LLM output."""
    lines = [l.strip() for l in raw.split("\n") if l.strip()]
    points = []
    for line in lines:
        cleaned = re.sub(r"^[\d]+[.)]\s*", "", line)
        cleaned = re.sub(r"^[•\-\*]\s*", "", cleaned)
        if cleaned and len(cleaned) > 10:
            points.append(cleaned)
    return points[:10]


def render_keypoints_tab(study_output: dict | None) -> None:
    """Render the Key Points tab with individual animated glass cards."""
    if not study_output:
        render_empty_state(
            "📌",
            "No Key Points Yet",
            "Generate study notes to extract the key learning concepts.",
        )
        return

    raw = study_output.get("key_points", "")

    if isinstance(raw, list):
        points = [str(p) for p in raw if p][:10]
    else:
        points = _parse_key_points(str(raw))

    proc_times = st.session_state.get("processing_times", {})
    t = proc_times.get("Key Points", proc_times.get("Study Material", None))

    # ── Header ───────────────────────────────────────────────────────────────
    h_col, t_col = st.columns([3, 1])
    with h_col:
        st.markdown(
            '<div class="card-section-label">📌 Key Learning Points</div>',
            unsafe_allow_html=True,
        )
    with t_col:
        if t:
            render_time_badge(t, "key points")

    if not points:
        st.markdown(raw)
        return

    # ── Stats row ─────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="margin-bottom:20px;font-size:13px;color:var(--text-muted);font-weight:500;">
        {len(points)} key concepts extracted from your document
    </div>
    """, unsafe_allow_html=True)

    # ── Animated individual cards ─────────────────────────────────────────────
    for i, point in enumerate(points):
        delay = i * 0.07
        icon  = _ICONS[i % len(_ICONS)]
        st.markdown(f"""
        <div class="kp-card" style="animation-delay:{delay:.2f}s;">
          <div class="kp-number">{i + 1}</div>
          <div style="flex:1;">
            <div style="font-size:11px;color:var(--primary-hover);font-weight:700;
                        text-transform:uppercase;letter-spacing:0.08em;margin-bottom:5px;">
              {icon} Point {i + 1}
            </div>
            <div class="kp-text">{point}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Download all ──────────────────────────────────────────────────────────
    st.markdown('<div style="margin-top:12px;"></div>', unsafe_allow_html=True)
    numbered = "\n".join(f"{i+1}. {p}" for i, p in enumerate(points))
    st.download_button(
        "⬇ Download Key Points",
        data=numbered,
        file_name="key_points.txt",
        mime="text/plain",
        key="btn_dl_kp",
    )
