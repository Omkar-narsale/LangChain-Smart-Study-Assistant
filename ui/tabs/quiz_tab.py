"""
ui/tabs/quiz_tab.py — Interactive Paginated Quiz Engine (v2)
=============================================================
Single-Question view with:
  - MCQ radio buttons (submit-gated)
  - Submit Answer button
  - Green/Red animated feedback
  - "👁 Show Correct Answer" only on wrong answers
  - Previous / Next navigation
  - Animated progress bar
  - Final Score screen with Restart
"""

from __future__ import annotations
import re
import streamlit as st
from ui.components import render_empty_state


# ---------------------------------------------------------------------------
# Parser (unchanged from original)
# ---------------------------------------------------------------------------

def _parse_quiz(raw) -> list[dict]:
    if isinstance(raw, dict):
        return _parse_quiz_json(raw)
    raw = str(raw)
    questions = []
    pattern = re.compile(
        r"Q(\d+)\s*:\s*(.+?)\s*A\1\s*:\s*(.+?)(?=Q\d+\s*:|$)",
        re.IGNORECASE | re.DOTALL,
    )
    for m in pattern.finditer(raw):
        num = int(m.group(1))
        q   = m.group(2).strip().replace("\n", " ")
        a   = m.group(3).strip().replace("\n", " ")
        q_lower = q.lower()
        if any(kw in q_lower for kw in ["true or false", "is it true", "is this true"]):
            qtype = "truefalse"
        elif "___" in q or "blank" in q_lower or "fill in" in q_lower:
            qtype = "fillin"
        else:
            qtype = "shortanswer"
        questions.append({"num": num, "q": q, "a": a, "type": qtype})
    if not questions:
        q_matches = re.findall(r"Q\d*\s*:\s*(.+)", raw, re.IGNORECASE)
        a_matches = re.findall(r"A\d*\s*:\s*(.+)", raw, re.IGNORECASE)
        for i, (q, a) in enumerate(zip(q_matches, a_matches), 1):
            questions.append({"num": i, "q": q.strip(), "a": a.strip(), "type": "shortanswer"})
    return questions[:10]


def _parse_quiz_json(quiz_dict: dict) -> list[dict]:
    questions = []
    num = 1
    for item in quiz_dict.get("mcq", []):
        q_text = item.get("question", "")
        options = item.get("options", [])
        answer  = item.get("answer", "")
        questions.append({"num": num, "q": q_text, "a": answer, "type": "mcq", "options": options})
        num += 1
    for item in quiz_dict.get("fill_blank", []):
        questions.append({"num": num, "q": item.get("question", ""), "a": item.get("answer", ""), "type": "fillin"})
        num += 1
    for item in quiz_dict.get("true_false", []):
        questions.append({"num": num, "q": item.get("question", ""), "a": item.get("answer", ""), "type": "truefalse"})
        num += 1
    for item in quiz_dict.get("short_answer", []):
        questions.append({"num": num, "q": item.get("question", ""), "a": item.get("answer", ""), "type": "shortanswer"})
        num += 1
    return questions


# ---------------------------------------------------------------------------
# Session state helpers
# ---------------------------------------------------------------------------

def _init_quiz_state(n_questions: int) -> None:
    defaults = {
        "quiz_idx":       0,
        "quiz_submitted": {},   # idx -> True/False (correct?)
        "quiz_revealed":  {},   # idx -> bool (showed answer?)
        "quiz_answers":   {},   # idx -> selected answer
        "quiz_done":      False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _reset_quiz() -> None:
    st.session_state.quiz_idx       = 0
    st.session_state.quiz_submitted = {}
    st.session_state.quiz_revealed  = {}
    st.session_state.quiz_answers   = {}
    st.session_state.quiz_done      = False


# ---------------------------------------------------------------------------
# Feedback HTML helpers
# ---------------------------------------------------------------------------

def _correct_banner() -> str:
    return """
    <div style="
        background: linear-gradient(135deg, rgba(16,185,129,0.15), rgba(16,185,129,0.05));
        border: 1px solid rgba(16,185,129,0.4);
        border-radius: 12px;
        padding: 16px 20px;
        margin-top: 12px;
        animation: fadeInUp 0.4s ease;
        display: flex; align-items: center; gap: 10px;
    ">
        <span style="font-size: 1.5rem;">✅</span>
        <span style="font-size: 1.1rem; font-weight: 700; color: #34D399;">Correct!</span>
    </div>
    <style>
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(10px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    </style>
    """


def _wrong_banner(answer: str, revealed: bool) -> str:
    reveal_block = f"""
    <div style="
        margin-top: 12px;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 10px;
        padding: 14px 18px;
        animation: fadeInUp 0.3s ease;
    ">
        <span style="font-size:0.8rem; color:var(--text-secondary); font-weight:600; text-transform:uppercase; letter-spacing:.05em;">Correct Answer</span>
        <div style="margin-top: 6px; font-size: 1rem; font-weight: 600; color: var(--text-primary);">{answer}</div>
    </div>
    """ if revealed else ""

    return f"""
    <div style="
        background: linear-gradient(135deg, rgba(239,68,68,0.12), rgba(239,68,68,0.04));
        border: 1px solid rgba(239,68,68,0.35);
        border-radius: 12px;
        padding: 16px 20px;
        margin-top: 12px;
        animation: fadeInUp 0.4s ease;
        display: flex; align-items: center; gap: 10px;
    ">
        <span style="font-size: 1.5rem;">❌</span>
        <span style="font-size: 1.1rem; font-weight: 700; color: #F87171;">Incorrect</span>
    </div>
    {reveal_block}
    """


# ---------------------------------------------------------------------------
# Single question renderer
# ---------------------------------------------------------------------------

def _render_question(q: dict, q_idx: int, n_total: int) -> None:
    """Render a single question card with submit logic."""
    idx = q["num"]
    submitted = st.session_state.quiz_submitted.get(idx)
    revealed  = st.session_state.quiz_revealed.get(idx, False)
    correct_a = q["a"]

    # ── Question card ──────────────────────────────────────────────────────
    qtype_label = {
        "mcq": "🔠 Multiple Choice",
        "truefalse": "🔘 True or False",
        "fillin": "✏️ Fill in the Blank",
        "shortanswer": "❓ Short Answer",
    }.get(q["type"], "❓ Question")

    st.markdown(f"""
    <div style="
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 20px;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        box-shadow: var(--shadow-md);
    ">
        <div style="
            font-size: 11px; font-weight: 700;
            color: var(--primary);
            text-transform: uppercase; letter-spacing: .1em;
            margin-bottom: 10px;
        ">{qtype_label} &nbsp;·&nbsp; Question {q_idx + 1} of {n_total}</div>
        <div style="
            font-size: 1.1rem; font-weight: 600;
            color: var(--text-primary); line-height: 1.55;
        ">{q["q"]}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Answer input ───────────────────────────────────────────────────────
    selected = st.session_state.quiz_answers.get(idx)

    if submitted is None:  # not yet submitted
        if q["type"] == "mcq":
            options = q.get("options", [])
            if options:
                sel = st.radio(
                    "Choose an answer",
                    options,
                    key=f"mcq_radio_{idx}",
                    label_visibility="collapsed",
                    disabled=False,
                )
                st.session_state.quiz_answers[idx] = sel
                selected = sel

        elif q["type"] == "truefalse":
            tf_col1, tf_col2, _ = st.columns([1, 1, 4])
            with tf_col1:
                if st.button("✅ True", key=f"tf_true_{idx}", use_container_width=True):
                    st.session_state.quiz_answers[idx] = "True"
                    st.rerun()
            with tf_col2:
                if st.button("❌ False", key=f"tf_false_{idx}", use_container_width=True):
                    st.session_state.quiz_answers[idx] = "False"
                    st.rerun()
            if selected:
                st.markdown(
                    f'<div style="font-size:0.85rem; color:var(--text-secondary); margin-top:6px;">Selected: <strong style="color:var(--text-primary);">{selected}</strong></div>',
                    unsafe_allow_html=True,
                )

        else:  # shortanswer / fillin
            user_input = st.text_input(
                "Your answer",
                key=f"sa_input_{idx}",
                placeholder="Type your answer here…",
                label_visibility="collapsed",
            )
            if user_input:
                st.session_state.quiz_answers[idx] = user_input
                selected = user_input

        # Submit button
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        submit_col, _ = st.columns([1, 3])
        with submit_col:
            can_submit = bool(selected)
            if st.button(
                "📤 Submit Answer",
                key=f"submit_{idx}",
                type="primary",
                use_container_width=True,
                disabled=not can_submit,
            ):
                # Evaluate answer (case-insensitive, partial match for MCQ)
                user_ans = str(st.session_state.quiz_answers.get(idx, "")).strip().lower()
                correct  = str(correct_a).strip().lower()
                is_correct = (user_ans == correct) or (user_ans in correct) or (correct in user_ans)
                st.session_state.quiz_submitted[idx] = is_correct
                st.rerun()

    else:
        # ── Show frozen answer after submission ────────────────────────────
        is_correct = submitted

        if q["type"] == "mcq":
            options = q.get("options", [])
            if options:
                st.radio(
                    "Choose an answer",
                    options,
                    index=options.index(selected) if selected in options else 0,
                    key=f"mcq_radio_frozen_{idx}",
                    label_visibility="collapsed",
                    disabled=True,
                )
        elif q["type"] == "truefalse":
            st.markdown(
                f'<div style="font-size:0.85rem; color:var(--text-secondary); margin-bottom:8px;">Your answer: <strong style="color:var(--text-primary);">{selected}</strong></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div style="background:rgba(255,255,255,0.03); border:1px solid var(--border); border-radius:8px; padding:10px 14px; margin-bottom:8px; color:var(--text-secondary); font-size:0.9rem;">Your answer: <strong style="color:var(--text-primary);">{selected}</strong></div>',
                unsafe_allow_html=True,
            )

        if is_correct:
            st.markdown(_correct_banner(), unsafe_allow_html=True)
        else:
            st.markdown(_wrong_banner(correct_a, revealed), unsafe_allow_html=True)
            if not revealed:
                _, rev_col, _ = st.columns([2, 1, 2])
                with rev_col:
                    if st.button("👁 Show Correct Answer", key=f"reveal_{idx}", use_container_width=True):
                        st.session_state.quiz_revealed[idx] = True
                        st.rerun()


# ---------------------------------------------------------------------------
# Main renderer
# ---------------------------------------------------------------------------

def render_quiz_tab(study_output: dict | None) -> None:
    """Render the full paginated interactive quiz tab."""
    if not study_output:
        render_empty_state("📝", "No Quiz Yet", "Generate study notes to create an interactive practice quiz.")
        return

    raw = study_output.get("quiz", "")
    questions = _parse_quiz(raw)

    if not questions:
        st.markdown(str(raw))
        return

    n_total = len(questions)
    _init_quiz_state(n_total)

    # ── Progress Bar ────────────────────────────────────────────────────────
    n_submitted = len(st.session_state.quiz_submitted)
    progress_pct = n_submitted / n_total if n_total else 0

    st.markdown(f"""
    <div style="margin-bottom:24px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span style="font-size:13px; font-weight:600; color:var(--text-secondary);">
                Progress — {n_submitted}/{n_total} answered
            </span>
            <span style="font-size:13px; font-weight:700; color:var(--primary);">{round(progress_pct*100)}%</span>
        </div>
        <div style="background:var(--border); border-radius:999px; height:6px; overflow:hidden;">
            <div style="
                width:{progress_pct*100:.1f}%;
                height:100%;
                background:linear-gradient(90deg, var(--primary), var(--accent));
                border-radius:999px;
                transition: width 0.5s ease;
            "></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Score summary row ───────────────────────────────────────────────────
    n_correct = sum(1 for v in st.session_state.quiz_submitted.values() if v)
    n_wrong   = n_submitted - n_correct

    stats_html = f"""
    <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-bottom:24px;">
        <div style="background:var(--bg-card); border:1px solid var(--border); border-radius:12px; padding:14px; text-align:center;">
            <div style="font-size:1.4rem; font-weight:800; color:var(--primary);">{n_total}</div>
            <div style="font-size:10px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:.06em;">Total</div>
        </div>
        <div style="background:var(--bg-card); border:1px solid var(--border); border-radius:12px; padding:14px; text-align:center;">
            <div style="font-size:1.4rem; font-weight:800; color:#FCD34D;">{n_submitted}</div>
            <div style="font-size:10px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:.06em;">Answered</div>
        </div>
        <div style="background:var(--bg-card); border:1px solid rgba(16,185,129,0.3); border-radius:12px; padding:14px; text-align:center;">
            <div style="font-size:1.4rem; font-weight:800; color:#34D399;">{n_correct}</div>
            <div style="font-size:10px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:.06em;">Correct</div>
        </div>
        <div style="background:var(--bg-card); border:1px solid rgba(239,68,68,0.3); border-radius:12px; padding:14px; text-align:center;">
            <div style="font-size:1.4rem; font-weight:800; color:#F87171;">{n_wrong}</div>
            <div style="font-size:10px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:.06em;">Wrong</div>
        </div>
    </div>
    """
    st.markdown(stats_html, unsafe_allow_html=True)

    # ── Current question ────────────────────────────────────────────────────
    q_idx = st.session_state.quiz_idx
    # Guard bounds
    if q_idx >= n_total:
        q_idx = n_total - 1
        st.session_state.quiz_idx = q_idx
    if q_idx < 0:
        q_idx = 0
        st.session_state.quiz_idx = 0

    q = questions[q_idx]
    _render_question(q, q_idx, n_total)

    # ── Navigation ──────────────────────────────────────────────────────────
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    nav_col1, nav_col2, nav_col3 = st.columns([1, 3, 1])

    with nav_col1:
        if st.button("← Previous", key="quiz_prev", use_container_width=True, disabled=(q_idx == 0)):
            st.session_state.quiz_idx = q_idx - 1
            st.rerun()

    with nav_col2:
        # Dot navigation
        dots_html = '<div style="display:flex; justify-content:center; gap:8px; padding-top:8px;">'
        for i in range(n_total):
            qi = questions[i]["num"]
            if i == q_idx:
                color = "var(--primary)"
                size  = "10px"
            elif qi in st.session_state.quiz_submitted:
                if st.session_state.quiz_submitted[qi]:
                    color = "#34D399"
                else:
                    color = "#F87171"
                size = "8px"
            else:
                color = "var(--border)"
                size  = "8px"
            dots_html += f'<div style="width:{size}; height:{size}; border-radius:50%; background:{color}; transition:all 0.2s; cursor:pointer;"></div>'
        dots_html += '</div>'
        st.markdown(dots_html, unsafe_allow_html=True)

    with nav_col3:
        if st.button("Next →", key="quiz_next", use_container_width=True, disabled=(q_idx >= n_total - 1)):
            st.session_state.quiz_idx = q_idx + 1
            st.rerun()

    # ── Final score screen ──────────────────────────────────────────────────
    if n_submitted >= n_total and n_total > 0:
        score_pct = round((n_correct / n_total) * 100)
        emoji = "🎉" if score_pct >= 80 else ("👍" if score_pct >= 50 else "📚")
        color = "#34D399" if score_pct >= 80 else ("#FCD34D" if score_pct >= 50 else "#F87171")
        st.markdown(f"""
        <div style="
            margin-top: 32px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 40px;
            text-align: center;
            backdrop-filter: blur(12px);
        ">
            <div style="font-size:3rem; margin-bottom:12px;">{emoji}</div>
            <div style="font-size:1.6rem; font-weight:800; color:var(--text-primary); margin-bottom:6px;">Quiz Complete!</div>
            <div style="font-size:3rem; font-weight:900; color:{color}; margin:12px 0;">{score_pct}%</div>
            <div style="font-size:0.9rem; color:var(--text-secondary);">
                You got <strong style="color:{color};">{n_correct}</strong> out of <strong>{n_total}</strong> correct
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        _, btn_col, _ = st.columns([2, 1, 2])
        with btn_col:
            if st.button("🔄 Restart Quiz", key="quiz_restart", type="primary", use_container_width=True):
                _reset_quiz()
                st.rerun()
