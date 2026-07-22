"""
ui/tabs/summary_tab.py — Premium Summary Tab with Browser TTS (v3)
====================================================================
Renders the AI-generated summary with:
  • Beautiful typography in glass card
  • Copy / Download / Regenerate buttons
  • Execution time badge
  • ▶ Listen Summary using browser Web Speech API (no external API)
    - Play, Pause/Resume, Stop
    - Speed control (0.75× to 2×)
    - Voice selector (all browser voices)
    - Animated waveform bars

v3: aligned CSS class names to match styles.py v3
"""

from __future__ import annotations
import json
import streamlit as st
import streamlit.components.v1 as components
from ui.components import render_empty_state, render_time_badge


_TTS_HTML = """
<div id="tts-player" style="
    background: rgba(14,21,38,0.75);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 14px;
    padding: 18px 22px;
    margin: 12px 0;
    font-family: 'Inter', sans-serif;
    backdrop-filter: blur(14px);
">
    <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">
        <div style="display:flex;align-items:center;gap:10px;">
            <div id="tts-icon" style="font-size:1.3rem;">🔊</div>
            <div>
                <div style="font-size:13px;font-weight:700;color:#F1F5F9;">Listen to Summary</div>
                <div id="tts-status" style="font-size:11px;color:#94A3B8;margin-top:2px;">Ready</div>
            </div>
        </div>
        <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;">
            <label style="font-size:11px;color:#94A3B8;font-weight:600;">Speed:</label>
            <select id="tts-speed" style="
                background:rgba(11,18,32,0.9);border:1px solid rgba(255,255,255,0.1);
                color:#F1F5F9;border-radius:7px;padding:4px 8px;font-size:12px;cursor:pointer;
                font-family:'Inter',sans-serif;
            ">
                <option value="0.75">0.75×</option>
                <option value="1.0" selected>1×</option>
                <option value="1.25">1.25×</option>
                <option value="1.5">1.5×</option>
                <option value="2.0">2×</option>
            </select>
            <select id="tts-voice" style="
                background:rgba(11,18,32,0.9);border:1px solid rgba(255,255,255,0.1);
                color:#F1F5F9;border-radius:7px;padding:4px 8px;font-size:12px;cursor:pointer;
                max-width:150px;font-family:'Inter',sans-serif;
            ">
                <option value="">Default Voice</option>
            </select>
        </div>
    </div>

    <!-- Animated waveform -->
    <div id="tts-wave" style="display:none;justify-content:center;align-items:center;gap:4px;margin:14px 0;height:30px;">
        <style>
            @keyframes wave {
                0%, 100% { height: 5px; }
                50%       { height: 26px; }
            }
            .wave-bar {
                width: 4px;border-radius: 4px;
                background: linear-gradient(180deg, #7C5CFF, #00C2FF);
                animation: wave 1.2s ease-in-out infinite;
            }
        </style>
        <div class="wave-bar" style="animation-delay:0s;"></div>
        <div class="wave-bar" style="animation-delay:0.10s;"></div>
        <div class="wave-bar" style="animation-delay:0.20s;"></div>
        <div class="wave-bar" style="animation-delay:0.30s;"></div>
        <div class="wave-bar" style="animation-delay:0.40s;"></div>
        <div class="wave-bar" style="animation-delay:0.50s;"></div>
        <div class="wave-bar" style="animation-delay:0.30s;"></div>
        <div class="wave-bar" style="animation-delay:0.10s;"></div>
    </div>

    <!-- Controls -->
    <div style="display:flex;gap:9px;margin-top:14px;flex-wrap:wrap;">
        <button id="btn-play" onclick="ttsPlay()" style="
            background:linear-gradient(135deg,#7C5CFF,#9D84FF);border:none;color:#fff;
            padding:9px 20px;border-radius:10px;cursor:pointer;font-weight:700;
            font-size:13px;transition:all 0.2s;display:flex;align-items:center;gap:6px;
            font-family:'Inter',sans-serif;
        ">▶ Play</button>
        <button id="btn-pause" onclick="ttsPause()" style="
            background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);
            color:#F1F5F9;padding:9px 16px;border-radius:10px;cursor:pointer;
            font-weight:600;font-size:13px;transition:all 0.2s;
            font-family:'Inter',sans-serif;
        " disabled>⏸ Pause</button>
        <button id="btn-stop" onclick="ttsStop()" style="
            background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.25);
            color:#F87171;padding:9px 16px;border-radius:10px;cursor:pointer;
            font-weight:600;font-size:13px;transition:all 0.2s;
            font-family:'Inter',sans-serif;
        " disabled>⏹ Stop</button>
    </div>
</div>

<script>
const summaryText = SUMMARY_TEXT_PLACEHOLDER;
let utterance = null;
let voices = [];
let paused = false;

function loadVoices() {
    voices = window.speechSynthesis.getVoices();
    const sel = document.getElementById('tts-voice');
    // Clear existing options except default
    while (sel.options.length > 1) sel.remove(1);
    voices.forEach((v, i) => {
        const opt = document.createElement('option');
        opt.value = i;
        opt.textContent = v.name + (v.lang ? ' (' + v.lang + ')' : '');
        sel.appendChild(opt);
    });
}

if (window.speechSynthesis) {
    window.speechSynthesis.onvoiceschanged = loadVoices;
    loadVoices();
}

function setStatus(msg) { document.getElementById('tts-status').textContent = msg; }
function showWave(show) { document.getElementById('tts-wave').style.display = show ? 'flex' : 'none'; }
function setBtns(playing) {
    document.getElementById('btn-play').disabled  = playing;
    document.getElementById('btn-pause').disabled = !playing;
    document.getElementById('btn-stop').disabled  = !playing;
}

function ttsPlay() {
    if (!window.speechSynthesis) { setStatus('❌ Not supported in this browser'); return; }
    if (paused) {
        window.speechSynthesis.resume();
        paused = false;
        setStatus('▶ Playing…');
        showWave(true);
        setBtns(true);
        document.getElementById('btn-pause').textContent = '⏸ Pause';
        return;
    }
    window.speechSynthesis.cancel();
    setTimeout(() => {
        utterance = new SpeechSynthesisUtterance(summaryText);
        const speed    = parseFloat(document.getElementById('tts-speed').value);
        const voiceIdx = document.getElementById('tts-voice').value;
        utterance.rate  = speed;
        if (voiceIdx !== '' && voices[parseInt(voiceIdx)]) {
            utterance.voice = voices[parseInt(voiceIdx)];
        }
        utterance.onstart = () => { setStatus('▶ Playing…'); showWave(true); setBtns(true); };
        utterance.onend   = () => { setStatus('✅ Finished'); showWave(false); setBtns(false); paused = false; document.getElementById('btn-pause').textContent = '⏸ Pause'; };
        utterance.onerror = (e) => { setStatus('❌ Error: ' + e.error); showWave(false); setBtns(false); };
        window.speechSynthesis.speak(utterance);
    }, 50);
}

function ttsPause() {
    if (!window.speechSynthesis) return;
    if (!paused) {
        window.speechSynthesis.pause();
        paused = true;
        setStatus('⏸ Paused');
        showWave(false);
        document.getElementById('btn-pause').textContent = '▶ Resume';
    } else {
        window.speechSynthesis.resume();
        paused = false;
        setStatus('▶ Playing…');
        showWave(true);
        document.getElementById('btn-pause').textContent = '⏸ Pause';
    }
}

function ttsStop() {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    paused = false;
    setStatus('⏹ Stopped');
    showWave(false);
    setBtns(false);
    document.getElementById('btn-pause').textContent = '⏸ Pause';
}

// Add change event listeners to speed and voice options to immediately update when changed while playing
document.getElementById('tts-speed').addEventListener('change', () => {
    if (window.speechSynthesis && (window.speechSynthesis.speaking || paused)) {
        paused = false;
        ttsPlay();
    }
});
document.getElementById('tts-voice').addEventListener('change', () => {
    if (window.speechSynthesis && (window.speechSynthesis.speaking || paused)) {
        paused = false;
        ttsPlay();
    }
});
</script>
"""


def translate_summary(text: str, target_language: str) -> str:
    """Translate summary text to target language using active LLM."""
    from config import task_token_budget, invoke_with_retry
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import PromptTemplate

    quality_instructions = ""
    if target_language == "Hindi":
        quality_instructions = "Ensure the Hindi translation is natural and formal. Do not mix English unnecessarily. Keep technical terms accurate."
    elif target_language == "Marathi":
        quality_instructions = "Ensure the Marathi translation uses standard Marathi suitable for college students. Do not mix English unnecessarily. Keep technical terms accurate."

    prompt = PromptTemplate.from_template(
        "You are a professional translator. Translate the following English text to {language}.\n\n"
        "CRITICAL TRANSLATION RULES:\n"
        "1. Translate ONLY. Do NOT summarize, shorten, or expand the content.\n"
        "2. Do NOT add any introductory, explanatory, or concluding text. Output ONLY the translated content.\n"
        "3. Preserve all formatting, headings, bullet points, numbering, bolding, and Markdown structure exactly as in the source text.\n"
        "4. Keep technical terms accurate. Do NOT mix English words unnecessarily.\n"
        "{quality_instructions}\n\n"
        "English Text to Translate:\n"
        "{text}\n\n"
        "Translation:"
    )

    parser = StrOutputParser()
    with task_token_budget("study_material") as model:
        chain = prompt | model | parser
        translated = invoke_with_retry(
            chain,
            {
                "language": target_language,
                "quality_instructions": quality_instructions,
                "text": text
            }
        )
    return translated.strip()


def render_summary_tab(study_output: dict | None) -> None:
    """Render the Summary tab content with TTS audio player and Translation dropdown."""
    if not study_output:
        render_empty_state(
            "📄",
            "No Summary Yet",
            "Upload a document and click ⚡ Generate Study Notes to create your summary.",
        )
        return

    summary     = study_output.get("summary", "")
    proc_times  = st.session_state.get("processing_times", {})
    t           = proc_times.get("Study Material", proc_times.get("Summary", None))

    # Initialize translation cache
    if "summary_cache" not in st.session_state or not st.session_state.summary_cache:
        st.session_state.summary_cache = {"English": summary}
    elif st.session_state.summary_cache.get("English") != summary:
        st.session_state.summary_cache = {"English": summary}

    # ── Translate Summary dropdown ───────────────────────────────────────────
    st.markdown("""
    <div style="display:flex; align-items:center; gap:8px; font-weight:700; color:var(--text-primary); font-size:14.5px; margin-bottom:6px; font-family:var(--font-display);">
        <span>🌐</span> Translate Summary
    </div>
    """, unsafe_allow_html=True)

    lang_options = ["English", "Hindi", "Marathi"]
    if "summary_lang" not in st.session_state:
        st.session_state.summary_lang = "English"

    selected_lang = st.selectbox(
        "Translate Summary Language",
        options=lang_options,
        index=lang_options.index(st.session_state.summary_lang),
        label_visibility="collapsed",
        key="summary_lang_select"
    )
    st.session_state.summary_lang = selected_lang

    # Get translation
    if selected_lang in st.session_state.summary_cache:
        active_summary = st.session_state.summary_cache[selected_lang]
    else:
        with st.spinner("Translating Summary..."):
            try:
                active_summary = translate_summary(summary, selected_lang)
                st.session_state.summary_cache[selected_lang] = active_summary
            except Exception as e:
                st.error(f"Translation failed: {e}")
                active_summary = summary

    # ── Header row ──────────────────────────────────────────────────────────
    h_col, t_col = st.columns([3, 1])
    with h_col:
        st.markdown(
            '<div class="card-section-label">📄 AI-Generated Summary</div>',
            unsafe_allow_html=True,
        )
    with t_col:
        if t:
            render_time_badge(t, "summary")

    # ── Glass card with summary ──────────────────────────────────────────────
    st.markdown(f"""
    <div class="glass-card glass-card-accent" style="margin-bottom:18px;">
      <div class="summary-content">{active_summary.replace(chr(10), "<br>")}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Browser TTS Player ───────────────────────────────────────────────────
    safe_summary = json.dumps(active_summary)
    tts_html     = _TTS_HTML.replace("SUMMARY_TEXT_PLACEHOLDER", safe_summary)
    components.html(tts_html, height=220, scrolling=False)

    # ── Action buttons ───────────────────────────────────────────────────────
    b1, b2, b3, _ = st.columns([1, 1, 1, 2])

    with b1:
        if st.button("📋 Copy", key="btn_copy_summary", use_container_width=True):
            st.components.v1.html(
                f"<script>navigator.clipboard.writeText({json.dumps(active_summary)}).then(()=>{{console.log('copied');}});</script>",
                height=0,
            )
            st.toast("✅ Summary copied!", icon="📋")

    with b2:
        st.download_button(
            "⬇ Download",
            data=active_summary,
            file_name="summary.txt",
            mime="text/plain",
            key="btn_dl_summary",
            use_container_width=True,
        )

    with b3:
        if st.button("🔄 Regenerate", key="btn_regen_summary", use_container_width=True):
            st.session_state.study_output = None
            st.session_state.summary_cache = {}
            st.session_state.summary_lang = "English"
            st.rerun()

    # ── Word count ────────────────────────────────────────────────────────────
    word_count = len(active_summary.split())
    st.markdown(
        f'<div style="margin-top:6px;font-size:11px;color:var(--text-muted);">Summary: {word_count} words</div>',
        unsafe_allow_html=True,
    )
