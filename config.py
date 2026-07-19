"""
config.py — LLM Configuration Factory & Failover
================================================
Provides a factory to load either Groq API or Local Gemma models 
based on the selected inference mode, with automatic failover 
if Groq is selected but fails.

Optimization notes:
  - Supports token streaming for Chat UI.
  - Retains single instances where possible.
  - Implements exponential backoff and rate limit handling.
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Optional, Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import streamlit as st
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------

LOCAL_MODEL_ID: str = "google/gemma-2-2b-it"
GROQ_MODEL_ID: str = "llama-3.1-8b-instant" # Fast Groq model

PIPELINE_KWARGS: dict = {
    "max_new_tokens": 512,
    "do_sample": False,
    "return_full_text": False,
}

# Task-specific generation settings (strictly matched to limits)
_TASK_SETTINGS: dict[str, dict] = {
    "map_summary":      {"max_tokens": 80,  "temperature": 0.0},
    "reduce_summary":   {"max_tokens": 160, "temperature": 0.0},
    "study_material":   {"max_tokens": 2048, "temperature": 0.0},
    "key_points":       {"max_tokens": 120, "temperature": 0.0},
    "quiz":             {"max_tokens": 220, "temperature": 0.0},
    "flashcards":       {"max_tokens": 160, "temperature": 0.0},
    "rag_answer":       {"max_tokens": 120, "temperature": 0.0},
    "ai_insights":      {"max_tokens": 100, "temperature": 0.0},
    "exam_generator":   {"max_tokens": 2048, "temperature": 0.2},
    "default":          {"max_tokens": 256, "temperature": 0.0},
}

# ---------------------------------------------------------------------------
# Singleton state for Local Gemma to avoid reloading
# ---------------------------------------------------------------------------

_local_llm_instance: Optional[HuggingFacePipeline] = None
_local_chat_model_instance: Optional[ChatHuggingFace] = None
_groq_instances: dict = {} # cache by parameters

# ---------------------------------------------------------------------------
# Core Factory Methods
# ---------------------------------------------------------------------------

def _get_local_pipeline() -> HuggingFacePipeline:
    global _local_llm_instance
    if _local_llm_instance is None:
        import torch
        from langchain_huggingface import HuggingFacePipeline
        logger.info("Loading Local Gemma from HuggingFace Hub: %s", LOCAL_MODEL_ID)
        _local_llm_instance = HuggingFacePipeline.from_model_id(
            model_id=LOCAL_MODEL_ID,
            task="text-generation",
            model_kwargs={
                "torch_dtype": torch.float32,
            },
            pipeline_kwargs=PIPELINE_KWARGS.copy(),
        )
    return _local_llm_instance


def _get_local_chat_model() -> ChatHuggingFace:
    global _local_chat_model_instance
    if _local_chat_model_instance is None:
        from langchain_huggingface import ChatHuggingFace
        logger.info("Wrapping Local LLM in ChatHuggingFace.")
        _local_chat_model_instance = ChatHuggingFace(llm=_get_local_pipeline())
    return _local_chat_model_instance


def _get_groq_chat_model(streaming: bool = False) -> ChatGroq:
    """Gets or creates a Groq model instance, prompting for API key if missing."""
    from langchain_groq import ChatGroq
    api_key = os.environ.get("GROQ_API_KEY", "")
    
    cache_key = f"groq_{streaming}"
    if cache_key not in _groq_instances:
        logger.info("Initializing Groq Chat Model. Streaming: %s", streaming)
        # Using a reliable fast Groq model.
        _groq_instances[cache_key] = ChatGroq(
            model_name=GROQ_MODEL_ID,
            temperature=0.0,
            streaming=streaming,
            max_tokens=256, # default
            api_key=api_key or "DUMMY_KEY" # Let it fail during invocation if invalid
        )
    return _groq_instances[cache_key]


def get_model(streaming: bool = False) -> Any:
    """
    Main factory method to retrieve the appropriate model wrapper based on UI state.
    Returns ChatGroq if 'Groq API' is selected, otherwise ChatHuggingFace.
    """
    mode = "Local Gemma"
    # Ensure safe access to session state, outside of UI context it defaults to Local
    if hasattr(st, "session_state") and "inference_mode" in st.session_state:
        mode = st.session_state.inference_mode

    if mode == "Groq API":
        return _get_groq_chat_model(streaming=streaming)
    
    # Default / Fallback
    return _get_local_chat_model()


def get_llm() -> Any:
    """
    Legacy wrapper for components expecting the raw pipeline. 
    Using Chat models is preferred for everything now.
    """
    return _get_local_pipeline()


# ---------------------------------------------------------------------------
# Parameter Management Context
# ---------------------------------------------------------------------------

@contextmanager
def task_token_budget(task: str):
    """
    Context manager that temporarily sets task parameters on the 
    appropriate model. Works for both Local Gemma pipeline and Groq.
    """
    mode = getattr(st.session_state, "inference_mode", "Local Gemma") if hasattr(st, "session_state") else "Local Gemma"
    settings = _TASK_SETTINGS.get(task, _TASK_SETTINGS["default"])
    
    if mode == "Local Gemma":
        llm = _get_local_pipeline()
        old_max = llm.pipeline_kwargs.get("max_new_tokens", 512)
        old_sample = llm.pipeline_kwargs.get("do_sample", False)
        old_temp = llm.pipeline_kwargs.get("temperature", None)
        
        try:
            llm.pipeline_kwargs["max_new_tokens"] = settings["max_tokens"]
            llm.pipeline_kwargs["do_sample"] = False
            llm.pipeline_kwargs.pop("temperature", None)
            llm.pipeline_kwargs.pop("top_p", None)
            llm.pipeline_kwargs.pop("top_k", None)
            yield _get_local_chat_model()
        finally:
            llm.pipeline_kwargs["max_new_tokens"] = old_max
            llm.pipeline_kwargs["do_sample"] = old_sample
            if old_temp is not None:
                llm.pipeline_kwargs["temperature"] = old_temp
                
    else: # Groq API
        try:
            model = _get_groq_chat_model(streaming=False) # For tasks, non-streaming is fine
            old_max = model.max_tokens
            old_temp = model.temperature
            
            # Reconfigure Groq model properties dynamically
            model.max_tokens = settings["max_tokens"]
            model.temperature = settings["temperature"]
            yield model
        finally:
            model.max_tokens = old_max
            model.temperature = old_temp

# ---------------------------------------------------------------------------
# Rate Limiting & Reliability for API calls
# ---------------------------------------------------------------------------

@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda retry_state: logger.warning(f"Rate limited or API error. Retrying {retry_state.attempt_number}...")
)
def invoke_with_retry(chain_or_model: Any, inputs: Any, **kwargs) -> Any:
    """
    Safely invoke a chain or model with exponential backoff.
    Should be used around all critical generation paths to handle Groq limits.
    """
    try:
        return chain_or_model.invoke(inputs, **kwargs)
    except Exception as e:
        logger.error(f"API Error during invoke: {e}")
        error_str = str(e).lower()
        if "429" in error_str or "rate limit" in error_str:
            if hasattr(st, "session_state"):
                st.warning("Groq Free Tier rate limit reached. Please wait a few seconds.")
        if "AuthenticationError" in str(type(e)):
            if hasattr(st, "session_state"):
                st.session_state.inference_mode = "Local Gemma"
                logger.warning("Groq Auth Failed. Falling back to Local Gemma.")
        raise
