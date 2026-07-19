"""
rag/__init__.py — RAG Package Initializer
==========================================
Exposes the public API of the RAG pipeline so callers can simply do:

    from rag import build_rag_chain, build_retriever, build_vector_store

All heavy imports happen lazily inside each sub-module to keep startup fast.
"""

from rag.rag_chain import build_rag_chain
from rag.retriever import build_retriever
from rag.vector_store import build_vector_store

__all__ = [
    "build_rag_chain",
    "build_retriever",
    "build_vector_store",
]
