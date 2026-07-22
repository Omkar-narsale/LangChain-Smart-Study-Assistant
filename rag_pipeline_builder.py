"""
rag_pipeline_builder.py — Standalone RAG Pipeline Builder
===========================================================
Extracted from app.py to avoid circular imports with chat_tab.py.
Builds the full RAG pipeline and caches it in Streamlit session state.

Architecture notes:
  - Every stage checks session_state cache before rebuilding.
  - Stages 5 (hybrid retriever) and 6 (RAG chain) are now cached too.
  - All UI updates are wrapped in safe_progress_update to prevent
    WebSocket errors when the client disconnects mid-processing.
  - Comprehensive timing logs for every stage.
"""

from __future__ import annotations

import time
import logging

import streamlit as st

from config import get_model
from rag.splitter import split_document
from rag.retriever import build_retriever
from rag.hybrid_retriever import build_bm25_retriever, build_hybrid_retriever
from rag.rag_chain import build_rag_chain
from rag.embeddings import get_embeddings
from utils.safe_ui import safe_progress_update

logger = logging.getLogger(__name__)


def build_rag_pipeline(document_text: str, progress_bar, status_label) -> None:
    """
    Build the full RAG pipeline for a document and cache in session state.

    Every stage is guarded: if the artifact already exists in session_state,
    it is reused.  This means page navigation or accidental re-calls will
    NOT rebuild embeddings, FAISS, BM25, etc.

    Stages:
        1. Split document into Parent and Child chunks
        2. Create embeddings for child chunks
        3. Build FAISS vector store
        4. Build BM25 index
        5. Build Hybrid Retriever (FAISS + BM25 + Parent fallback)
        6. Build RAG chain

    Args:
        document_text: Raw extracted text from the uploaded document.
        progress_bar:  Streamlit progress bar placeholder.
        status_label:  Streamlit empty placeholder for stage labels.
    """
    # ── Early exit if already fully built ───────────────────────────────────
    if (
        st.session_state.get("embedding_status") == "ready"
        and st.session_state.get("rag_chain") is not None
    ):
        logger.info("RAG pipeline already built — skipping rebuild.")
        safe_progress_update(progress_bar, status_label, 100, "✅ Already ready!", 0)
        return

    pipeline_t0 = time.time()
    st.session_state.embedding_status = "building"

    times = st.session_state.get("processing_times", {})

    safe_progress_update(progress_bar, status_label, 10, "📄 Loading document…", 0.02)
    safe_progress_update(progress_bar, status_label, 25, "✂️ Splitting into Parent & Child chunks…", 0.02)

    # ── Stage 1: Split ──────────────────────────────────────────────────────
    if st.session_state.get("doc_chunks") is not None:
        parent_docs = st.session_state.parent_docs
        child_docs = st.session_state.doc_chunks
        logger.info("Reusing cached document chunks.")
    else:
        t0 = time.time()
        page_texts = st.session_state.get("page_texts")
        filename = st.session_state.get("file_display_name", "Unknown Document")
        input_data = page_texts if page_texts else document_text
        parent_docs, child_docs = split_document(input_data, filename=filename)
        st.session_state.parent_docs = parent_docs
        st.session_state.doc_chunks = child_docs
        elapsed = round(time.time() - t0, 3)
        times["Document Split"] = elapsed
        logger.info("Document split into %d child chunks in %.3fs.", len(child_docs), elapsed)

    st.session_state.chunk_count = len(child_docs)

    safe_progress_update(progress_bar, status_label, 40, "🧬 Creating embeddings…", 0.02)

    # ── Stage 2: Embeddings ──────────────────────────────────────────────────
    if st.session_state.get("doc_embeddings") is not None:
        vectors = st.session_state.doc_embeddings
        logger.info("Reusing cached document embeddings.")
    else:
        t0 = time.time()
        embeddings_model = get_embeddings()
        texts = [c.page_content for c in child_docs]
        vectors = embeddings_model.embed_documents(texts)
        st.session_state.doc_embeddings = vectors
        elapsed = round(time.time() - t0, 3)
        times["Embeddings"] = elapsed
        logger.info("Embeddings created for %d chunks in %.3fs.", len(texts), elapsed)

    safe_progress_update(progress_bar, status_label, 55, "🗂️ Building FAISS index…", 0.02)

    # ── Stage 3: FAISS Index ────────────────────────────────────────────────
    if st.session_state.get("rag_vectorstore") is not None:
        vs = st.session_state.rag_vectorstore
        logger.info("Reusing cached FAISS index.")
    else:
        t0 = time.time()
        from langchain_community.vectorstores import FAISS
        embeddings_model = get_embeddings()
        texts = [c.page_content for c in child_docs]
        metadatas = [c.metadata for c in child_docs]
        text_embeddings = list(zip(texts, vectors))
        vs = FAISS.from_embeddings(
            text_embeddings=text_embeddings,
            embedding=embeddings_model,
            metadatas=metadatas
        )
        st.session_state.rag_vectorstore = vs
        elapsed = round(time.time() - t0, 3)
        times["FAISS Index"] = elapsed
        logger.info("FAISS index built successfully in %.3fs.", elapsed)

    safe_progress_update(progress_bar, status_label, 70, "🔤 Building BM25 index…", 0.02)

    # ── Stage 4: BM25 Index ─────────────────────────────────────────────────
    if st.session_state.get("rag_bm25") is not None:
        bm25_retriever = st.session_state.rag_bm25
        logger.info("Reusing cached BM25 index.")
    else:
        t0 = time.time()
        bm25_retriever = build_bm25_retriever(child_docs)
        st.session_state.rag_bm25 = bm25_retriever
        elapsed = round(time.time() - t0, 3)
        times["BM25 Index"] = elapsed
        logger.info("BM25 index built in %.3fs.", elapsed)

    # ── Stage 5: Hybrid Retriever ───────────────────────────────────────────
    safe_progress_update(progress_bar, status_label, 85, "🔍 Initializing Hybrid retriever…", 0.02)

    if st.session_state.get("rag_retriever") is not None:
        logger.info("Reusing cached hybrid retriever.")
    else:
        t0 = time.time()
        vector_retriever = build_retriever(vs)  # Uses default k=3
        hybrid_retriever = build_hybrid_retriever(
            vector_retriever=vector_retriever,
            bm25_retriever=bm25_retriever,
            parent_docs=parent_docs,
            k=3
        )
        st.session_state.rag_retriever = hybrid_retriever
        elapsed = round(time.time() - t0, 3)
        times["Hybrid Retriever"] = elapsed
        logger.info("Hybrid retriever built in %.3fs.", elapsed)

    # ── Stage 6: RAG Chain ──────────────────────────────────────────────────
    safe_progress_update(progress_bar, status_label, 95, "⚡ Assembling RAG chain…", 0.02)

    if st.session_state.get("rag_chain") is not None:
        logger.info("Reusing cached RAG chain.")
    else:
        t0 = time.time()
        llm = get_model()
        chain = build_rag_chain(st.session_state.rag_retriever, llm)
        st.session_state.rag_chain = chain
        elapsed = round(time.time() - t0, 3)
        times["RAG Chain"] = elapsed
        logger.info("RAG chain built in %.3fs.", elapsed)

    safe_progress_update(progress_bar, status_label, 100, "✅ Ready to chat!", 0.05)
    st.session_state.embedding_status = "ready"
    st.session_state.processing_times = times

    total_elapsed = round(time.time() - pipeline_t0, 3)
    logger.info(
        "RAG pipeline complete in %.3fs. Stages: %s",
        total_elapsed,
        ", ".join(f"{k}={v}s" for k, v in times.items()),
    )
