"""
rag/embeddings.py — Singleton Sentence-Transformer Embeddings
==============================================================
Provides a single public function:

    get_embeddings() -> HuggingFaceEmbeddings

Loads the sentence-transformers/all-MiniLM-L6-v2 model exactly ONCE
and reuses it across all subsequent calls.  This follows the same
singleton pattern used in config.py for the Gemma LLM.

Model choice rationale:
    all-MiniLM-L6-v2 is a compact (22 M parameter) model that produces
    384-dimensional embeddings. It is fast on CPU and provides strong
    semantic similarity quality for retrieval tasks — ideal for local inference.

Performance notes:
    - First call: model download + load (several seconds)
    - Subsequent calls: sub-millisecond (returns cached instance)
    - encode_kwargs normalize_embeddings=True ensures cosine similarity
      works correctly with FAISS inner-product search.
"""

from __future__ import annotations

import logging
from typing import Optional

from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model identifier — change here to swap embedding model globally
# ---------------------------------------------------------------------------

_EMBEDDING_MODEL_ID: str = "sentence-transformers/all-MiniLM-L6-v2"

# ---------------------------------------------------------------------------
# Singleton state — module-level, survives Streamlit reruns
# ---------------------------------------------------------------------------

_embeddings_instance: Optional[HuggingFaceEmbeddings] = None


def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Return the singleton HuggingFaceEmbeddings instance.

    The sentence-transformer model is loaded from disk/HuggingFace Hub
    on the very first call and then reused for every subsequent call —
    even across multiple Streamlit reruns within the same session.

    Returns:
        HuggingFaceEmbeddings: Ready-to-use embeddings model.

    Example:
        >>> embeddings = get_embeddings()
        >>> vector = embeddings.embed_query("What is machine learning?")
    """
    global _embeddings_instance

    if _embeddings_instance is None:
        logger.info("Loading embedding model: %s", _EMBEDDING_MODEL_ID)
        _embeddings_instance = HuggingFaceEmbeddings(
            model_name=_EMBEDDING_MODEL_ID,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},  # required for cosine sim
        )
        logger.info("Embedding model loaded successfully.")
    else:
        logger.info("Reusing cached embedding model instance.")

    return _embeddings_instance
