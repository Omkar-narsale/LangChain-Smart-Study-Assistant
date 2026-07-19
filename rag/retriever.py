"""
rag/retriever.py — FAISS Retriever Builder
===========================================
Provides a single public function:

    build_retriever(vector_store: FAISS, k: int = 4) -> VectorStoreRetriever

Wraps a FAISS vector store with a similarity-search retriever that
returns the top-k most relevant document chunks for any query.

Why k=4?
    Four chunks at ~800 chars each gives ~3 200 characters of context —
    enough to ground Gemma's answer without overflowing its context window
    on CPU.  Increase k for larger models running on GPU.

Design notes:
    - Pure function: takes a vector store, returns a retriever.
    - k is exposed as a parameter so callers can override it for testing
      or for future tuning without editing this file.
    - The retriever returned is a standard LangChain BaseRetriever so it
      integrates natively into LCEL chains via the pipe operator.
"""

from __future__ import annotations

import logging

from langchain_community.vectorstores import FAISS
from langchain_core.vectorstores import VectorStoreRetriever

logger = logging.getLogger(__name__)

# Default number of retrieved chunks
_DEFAULT_K: int = 3


def build_retriever(
    vector_store: FAISS,
    k: int = _DEFAULT_K,
) -> VectorStoreRetriever:
    """
    Create a similarity-search retriever from a FAISS vector store.

    Args:
        vector_store: A FAISS vector store built by build_vector_store().
        k:            Number of top chunks to retrieve per query. Default 4.

    Returns:
        VectorStoreRetriever: A LangChain retriever configured for
                              similarity-based search with top-k results.

    Example:
        >>> retriever = build_retriever(vector_store, k=4)
        >>> docs = retriever.invoke("What is backpropagation?")
    """
    logger.info("Building FAISS retriever (top k=%d).", k)

    retriever: VectorStoreRetriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )

    logger.info("Retriever built successfully.")
    return retriever
