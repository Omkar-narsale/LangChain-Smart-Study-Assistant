"""
rag_pipeline_builder.py — Standalone RAG Pipeline Builder
===========================================================
Extracted from app.py to avoid circular imports with chat_tab.py.
Builds the full RAG pipeline and caches it in Streamlit session state.
"""

from __future__ import annotations

import time
import logging

import streamlit as st

from config import get_model
from rag.splitter import split_document
from rag.vector_store import build_vector_store
from rag.retriever import build_retriever
from rag.hybrid_retriever import build_bm25_retriever, build_hybrid_retriever
from rag.rag_chain import build_rag_chain

logger = logging.getLogger(__name__)


def build_rag_pipeline(document_text: str, progress_bar, status_label) -> None:
    """
    Build the full RAG pipeline for a document and cache in session state.

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
    st.session_state.embedding_status = "building"

    def _upd(pct: int, msg: str, pause: float = 0.2) -> None:
        progress_bar.progress(pct)
        status_label.markdown(
            f'<p class="stage-label">{msg}</p>',
            unsafe_allow_html=True,
        )
        time.sleep(pause)

    times = st.session_state.get("processing_times", {})

    _upd(10, "📄 Loading document…", 0.15)
    _upd(25, "✂️ Splitting into Parent & Child chunks…", 0.2)

    # ── Stage 1: Split ──────────────────────────────────────────────────────
    if st.session_state.get("doc_chunks") is not None:
        parent_docs = st.session_state.parent_docs
        child_docs = st.session_state.doc_chunks # child chunks
        logger.info("Reusing cached document chunks.")
    else:
        t0 = time.time()
        parent_docs, child_docs = split_document(document_text)
        st.session_state.parent_docs = parent_docs
        st.session_state.doc_chunks = child_docs
        times["Document Split"] = round(time.time() - t0, 3)
        logger.info("Document split into %d child chunks.", len(child_docs))

    st.session_state.chunk_count = len(child_docs)

    _upd(40, "🧬 Creating embeddings…", 0.15)

    # ── Stage 2: Embeddings ──────────────────────────────────────────────────
    if st.session_state.get("doc_embeddings") is not None:
        vectors = st.session_state.doc_embeddings
        logger.info("Reusing cached document embeddings.")
    else:
        t0 = time.time()
        from rag.embeddings import get_embeddings
        embeddings_model = get_embeddings()
        texts = [c.page_content for c in child_docs]
        vectors = embeddings_model.embed_documents(texts)
        st.session_state.doc_embeddings = vectors
        times["Embeddings"] = round(time.time() - t0, 3)
        logger.info("Embeddings created successfully.")

    _upd(55, "🗂️ Building FAISS index…", 0.2)

    # ── Stage 3: FAISS Index ────────────────────────────────────────────────
    if st.session_state.get("rag_vectorstore") is not None:
        vs = st.session_state.rag_vectorstore
        logger.info("Reusing cached FAISS index.")
    else:
        t0 = time.time()
        from langchain_community.vectorstores import FAISS
        from rag.embeddings import get_embeddings
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
        times["FAISS Index"] = round(time.time() - t0, 3)
        logger.info("FAISS index built successfully.")

    _upd(70, "🔤 Building BM25 index…", 0.2)
    
    # ── Stage 4: BM25 Index ─────────────────────────────────────────────────
    if st.session_state.get("rag_bm25") is not None:
        bm25_retriever = st.session_state.rag_bm25
        logger.info("Reusing cached BM25 index.")
    else:
        t0 = time.time()
        bm25_retriever = build_bm25_retriever(child_docs)
        st.session_state.rag_bm25 = bm25_retriever
        times["BM25 Index"] = round(time.time() - t0, 3)

    # ── Stage 5: Hybrid Retriever ───────────────────────────────────────────
    _upd(85, "🔍 Initializing Hybrid retriever…", 0.15)
    vector_retriever = build_retriever(vs)  # Uses default k=3
    hybrid_retriever = build_hybrid_retriever(
        vector_retriever=vector_retriever,
        bm25_retriever=bm25_retriever,
        parent_docs=parent_docs,
        k=3
    )
    st.session_state.rag_retriever = hybrid_retriever

    # ── Stage 6: RAG Chain ──────────────────────────────────────────────────
    _upd(95, "⚡ Assembling RAG chain…", 0.15)
    # The chain needs the model
    llm = get_model() 
    chain = build_rag_chain(hybrid_retriever, llm)
    st.session_state.rag_chain = chain

    _upd(100, "✅ Ready to chat!", 0.2)
    st.session_state.embedding_status = "ready"
    st.session_state.processing_times = times
    logger.info("RAG pipeline built and cached in session state.")
