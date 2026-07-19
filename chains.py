"""
chains.py — Optimized LCEL Study Chain (Single-Call Architecture)
=================================================================
Implements a two-stage LangChain LCEL pipeline optimized for minimum
API calls:

    Stage 1 — Map-Reduce Summary:
        document → parallel map summaries → reduce → final summary

    Stage 2 — Single Unified Call:
        summary → ONE LLM call → JSON with key_points, quiz, flashcards, ai_insights

    Old: ~12-20 API calls (map + reduce + key_points + quiz + flashcards + ai_insights)
    New: ~N+2 API calls (N parallel maps + 1 reduce + 1 study material)

LCEL constructs used:
    RunnableSequence   — implicit via `|` operator
    RunnableLambda     — pure Python functions wired into the chain graph
    StrOutputParser    — strips metadata from ChatModel responses
    concurrent.futures — parallel execution of map summaries
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import (
    RunnableLambda,
)

from config import get_model
from prompts import (
    map_prompt,
    reduce_prompt,
    study_material_prompt,
)

from rag.splitter import split_document
logger = logging.getLogger(__name__)


def _record_time(key: str, elapsed: float) -> None:
    """Safely write a processing time into session state."""
    import streamlit as st
    if "processing_times" not in st.session_state:
        st.session_state.processing_times = {}
    st.session_state.processing_times[key] = round(elapsed, 3)

# ---------------------------------------------------------------------------
# Shared components
# ---------------------------------------------------------------------------

# Single parser instance — thread-safe, stateless, reusable
_parser = StrOutputParser()


# ---------------------------------------------------------------------------
# JSON parser with fallback
# ---------------------------------------------------------------------------

def _parse_study_json(raw: str) -> dict:
    """
    Parse the LLM's JSON output into a Python dict.
    Handles common issues: markdown fences, trailing commas, partial JSON.
    """
    # Strip markdown code fences if present
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()

    # Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in the text
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Complete failure — return empty structure so UI doesn't crash
    logger.warning("Failed to parse study material JSON. Returning fallback.")
    return {
        "key_points": [],
        "quiz": {"mcq": [], "fill_blank": [], "true_false": [], "short_answer": []},
        "flashcards": [],
        "ai_insights": {"difficulty": "—", "main_topic": "—", "top_concepts": [], "exam_focus": "—"},
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_study_chain():
    """
    Build and return the optimized study chain.
    Executes a single LLM call on truncated document text.
    """

    def _run_full_pipeline(document_dict: dict[str, str]) -> dict[str, Any]:
        import streamlit as st
        import time
        from config import task_token_budget, invoke_with_retry

        logger.info("Running optimized single-call study pipeline...")

        # ── Stage 1: Truncate Text for Context Limits ──────────────────
        doc_text = document_dict["document"]
        # Approximate 4000 tokens limit (~16,000 characters) to leave room for output
        truncated_text = doc_text[:16000]

        # ── Stage 2: Single Study Material Generation Call ──────────────
        t_study = time.time()
        
        # Enable streaming for the main JSON generation
        from langchain_community.callbacks import StreamlitCallbackHandler
        stream_container = st.empty()
        
        with task_token_budget("study_material") as model:
            study_chain = study_material_prompt | model | _parser
            raw_json = invoke_with_retry(
                study_chain,
                {"text": truncated_text},
                config={"callbacks": [StreamlitCallbackHandler(stream_container.container())]}
            )
            
        stream_container.empty() # clear the raw json tokens after complete
        
        _record_time("Study Material", time.time() - t_study)
        logger.info("Stage 2 complete – study materials generated in ONE call.")

        # ── Parse JSON ──────────────────────────────────────────────────
        materials = _parse_study_json(raw_json)

        # ── Merge into final output dict ────────────────────────────────
        return {
            "summary":     materials.get("summary", "No summary generated."),
            "key_points":  materials.get("key_points", []),
            "quiz":        materials.get("quiz", {}),
            "flashcards":  materials.get("flashcards", []),
            "ai_insights": materials.get("ai_insights", []),
        }

    study_chain = RunnableLambda(_run_full_pipeline)
    logger.info("Optimized study chain built successfully.")
    return study_chain
