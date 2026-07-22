"""
mindmap_generator.py — Generates Mermaid.js Mind Map code using the LLM.
"""

from __future__ import annotations

import re
import logging
import streamlit as st

from config import get_model, invoke_with_retry
from prompts import mindmap_prompt
from langchain_core.runnables import RunnableLambda, RunnableSequence

logger = logging.getLogger(__name__)

def _clean_mindmap_output(raw_text: str) -> str:
    """
    Strips markdown formatting, code blocks, and leading/trailing whitespace.
    Ensures clean Markdown outline is returned.
    """
    cleaned = raw_text.strip()
    
    # Remove markdown code blocks (e.g. ```markdown ... ``` or ``` ... ```)
    cleaned = re.sub(r"^```[a-zA-Z]*\n", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"```$", "", cleaned, flags=re.MULTILINE)
    
    # If there are any leading non-list lines, locate the first list item or heading
    match = re.search(r"(^[ \t]*[-*+#].*)$", cleaned, re.MULTILINE)
    if match:
        cleaned = cleaned[match.start():]
        
    return cleaned.strip()

@st.cache_data
def _generate_mindmap_code(summary_text: str, inference_mode: str) -> str:
    llm = get_model()
    
    # Build a simple chain
    chain = mindmap_prompt | llm
    
    logger.info("Invoking mind map generation LLM call...")
    # Using the retry logic from config to handle 429 errors gracefully
    raw_response = invoke_with_retry(chain, {"summary": summary_text})
    
    # Depending on the LLM type (Groq vs Local HuggingFace), it might return an AIMessage or a string
    if hasattr(raw_response, "content"):
        output_text = raw_response.content
    else:
        output_text = str(raw_response)
        
    cleaned_code = _clean_mindmap_output(output_text)
    
    if not cleaned_code:
        raise ValueError("Failed to generate valid Mind Map outline.")
        
    return cleaned_code

def generate_mindmap() -> str:
    """
    Generates Markdown outline based on the cached summary.
    Throws an exception if the summary is not available.
    """
    study_output = st.session_state.get("study_output")
    if not study_output or "summary" not in study_output:
        raise ValueError("No summary found. Please generate Study Materials first.")
        
    summary_text = study_output["summary"]
    inference_mode = st.session_state.get("inference_mode", "Local Gemma")
    
    cleaned_code = _generate_mindmap_code(summary_text, inference_mode)
    st.session_state.mindmap_markdown = cleaned_code
    return cleaned_code

