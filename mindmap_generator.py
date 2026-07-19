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

def _clean_mermaid_output(raw_text: str) -> str:
    """
    Strips markdown formatting, JSON structures, and leading/trailing whitespace.
    Ensures pure Mermaid.js code is returned.
    """
    cleaned = raw_text.strip()
    
    # Remove markdown code blocks (e.g. ```mermaid ... ``` or ``` ... ```)
    cleaned = re.sub(r"^```[a-zA-Z]*\n", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"```$", "", cleaned, flags=re.MULTILINE)
    
    # Sometimes the LLM includes explanatory text. We will just attempt to strip lines before 'mindmap' or 'graph TD'
    match = re.search(r"(mindmap|graph TD).*$", cleaned, re.IGNORECASE | re.DOTALL)
    if match:
        cleaned = match.group(0)
        
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
        
    cleaned_code = _clean_mermaid_output(output_text)
    
    if not cleaned_code:
        raise ValueError("Failed to generate valid Mermaid code.")
        
    return cleaned_code

def generate_mindmap() -> str:
    """
    Generates Mermaid code based on the cached summary.
    Throws an exception if the summary is not available.
    """
    study_output = st.session_state.get("study_output")
    if not study_output or "summary" not in study_output:
        raise ValueError("No summary found. Please generate Study Materials first.")
        
    summary_text = study_output["summary"]
    inference_mode = st.session_state.get("inference_mode", "Local Gemma")
    
    cleaned_code = _generate_mindmap_code(summary_text, inference_mode)
    st.session_state.mermaid_code = cleaned_code
    return cleaned_code
