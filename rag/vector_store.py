"""
rag/vector_store.py — FAISS Vector Store Builder
==================================================
Provides a single public function:

    build_vector_store(child_chunks: list[Document]) -> FAISS

Builds a FAISS index exclusively over child chunks.
"""

from __future__ import annotations

import logging

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from rag.embeddings import get_embeddings

logger = logging.getLogger(__name__)


def build_vector_store(child_chunks: list[Document]) -> FAISS:
    """
    Build a FAISS vector store from a list of child document chunks.
    """
    if not child_chunks:
        raise ValueError("Cannot build a vector store from an empty chunk list.")

    logger.info("Building FAISS vector store from %d child chunks...", len(child_chunks))

    embeddings = get_embeddings()

    try:
        vector_store = FAISS.from_documents(
            documents=child_chunks,
            embedding=embeddings,
        )
    except Exception as exc:
        logger.exception("Failed to build FAISS vector store.")
        raise RuntimeError(f"Vector store creation failed: {exc}") from exc

    logger.info("FAISS vector store built successfully.")
    return vector_store
