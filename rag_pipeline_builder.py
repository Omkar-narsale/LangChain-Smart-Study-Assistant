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

# ── Cached helpers to avoid rebuilding RAG database ─────────────────────────

@st.cache_data
def get_split_chunks(document_text: str, file_hash: str):
    logger.info("Splitting document... (not cached or new hash %s)", file_hash)
    return split_document(document_text)

@st.cache_resource
def get_doc_embeddings(file_hash: str, _child_docs):
    logger.info("Creating embeddings... (not cached or new hash %s)", file_hash)
    from rag.embeddings import get_embeddings
    embeddings_model = get_embeddings()
    texts = [c.page_content for c in _child_docs]
    return embeddings_model.embed_documents(texts)

@st.cache_resource
def get_faiss_vector_store(file_hash: str, _child_docs, vectors):
    logger.info("Building FAISS index... (not cached or new hash %s)", file_hash)
    from langchain_community.vectorstores import FAISS
    from rag.embeddings import get_embeddings
    embeddings_model = get_embeddings()
    texts = [c.page_content for c in _child_docs]
    metadatas = [c.metadata for c in _child_docs]
    text_embeddings = list(zip(texts, vectors))
    return FAISS.from_embeddings(
        text_embeddings=text_embeddings,
        embedding=embeddings_model,
        metadatas=metadatas
    )

@st.cache_resource
def get_bm25_retriever_cached(file_hash: str, _child_docs):
    logger.info("Building BM25 index... (not cached or new hash %s)", file_hash)
    return build_bm25_retriever(_child_docs)

@st.cache_resource
def get_hybrid_retriever_cached(file_hash: str, _vector_retriever, _bm25_retriever, _parent_docs):
    logger.info("Initializing Hybrid retriever... (not cached or new hash %s)", file_hash)
    return build_hybrid_retriever(
        vector_retriever=_vector_retriever,
        bm25_retriever=_bm25_retriever,
        parent_docs=_parent_docs,
        k=3
    )

# ─────────────────────────────────────────────────────────────────────────────

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

    # Compute hash if missing
    file_hash = st.session_state.get("file_hash", "")
    if not file_hash:
        import hashlib
        file_hash = hashlib.sha256(document_text.encode("utf-8")).hexdigest()
        st.session_state.file_hash = file_hash

    def _upd(pct: int, msg: str, pause: float = 0.05) -> None:
        progress_bar.progress(pct)
        status_label.markdown(
            f'<p class="stage-label">{msg}</p>',
            unsafe_allow_html=True,
        )
        time.sleep(pause)

    times = st.session_state.get("processing_times", {})

    _upd(10, "📄 Loading document…", 0.02)
    _upd(25, "✂️ Splitting into Parent & Child chunks…", 0.02)

    # ── Stage 1: Split ──────────────────────────────────────────────────────
    t0 = time.time()
    parent_docs, child_docs = get_split_chunks(document_text, file_hash)
    st.session_state.parent_docs = parent_docs
    st.session_state.doc_chunks = child_docs
    if "Document Split" not in times:
        times["Document Split"] = round(time.time() - t0, 3)
    logger.info("Document split completed. %d chunks.", len(child_docs))

    st.session_state.chunk_count = len(child_docs)

    _upd(40, "🧬 Creating embeddings…", 0.02)

    # ── Stage 2: Embeddings ──────────────────────────────────────────────────
    t0 = time.time()
    vectors = get_doc_embeddings(file_hash, child_docs)
    st.session_state.doc_embeddings = vectors
    if "Embeddings" not in times:
        times["Embeddings"] = round(time.time() - t0, 3)
    logger.info("Embeddings completed.")

    _upd(55, "🗂️ Building FAISS index…", 0.02)

    # ── Stage 3: FAISS Index ────────────────────────────────────────────────
    t0 = time.time()
    vs = get_faiss_vector_store(file_hash, child_docs, vectors)
    st.session_state.rag_vectorstore = vs
    if "FAISS Index" not in times:
        times["FAISS Index"] = round(time.time() - t0, 3)
    logger.info("FAISS index built.")

    _upd(70, "🔤 Building BM25 index…", 0.02)
    
    # ── Stage 4: BM25 Index ─────────────────────────────────────────────────
    t0 = time.time()
    bm25_retriever = get_bm25_retriever_cached(file_hash, child_docs)
    st.session_state.rag_bm25 = bm25_retriever
    if "BM25 Index" not in times:
        times["BM25 Index"] = round(time.time() - t0, 3)

    # ── Stage 5: Hybrid Retriever ───────────────────────────────────────────
    _upd(85, "🔍 Initializing Hybrid retriever…", 0.02)
    vector_retriever = build_retriever(vs)  # Uses default k=3
    hybrid_retriever = get_hybrid_retriever_cached(file_hash, vector_retriever, bm25_retriever, parent_docs)
    st.session_state.rag_retriever = hybrid_retriever

    # ── Stage 6: RAG Chain ──────────────────────────────────────────────────
    _upd(95, "⚡ Assembling RAG chain…", 0.02)
    llm = get_model() 
    chain = build_rag_chain(hybrid_retriever, llm)
    st.session_state.rag_chain = chain

    _upd(100, "✅ Ready to chat!", 0.05)
    st.session_state.embedding_status = "ready"
    st.session_state.processing_times = times
    logger.info("RAG pipeline successfully configured.")
