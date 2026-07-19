"""
rag/hybrid_retriever.py — Advanced Hybrid Retrieval Pipeline
============================================================
Combines FAISS and BM25 retrievers, merges results, removes duplicates, 
fetches parent contexts, and optionally compresses context.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Optional, Any

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_community.retrievers import BM25Retriever
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AdvancedHybridRetriever(BaseRetriever):
    """
    A custom LangChain retriever that:
    1. Queries FAISS (vector search) for child chunks.
    2. Queries BM25 (keyword search) for child chunks.
    3. Merges and ranks the results.
    4. Removes duplicate chunks.
    5. Retrieves the corresponding parent chunks for the top results.
    """
    vector_retriever: BaseRetriever
    bm25_retriever: BaseRetriever
    parent_store: dict = Field(default_factory=dict)
    k: int = 4

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        
        # 1. Fetch child docs from both retrievers
        # We query for slightly more chunks than k to allow for deduplication
        query_k = max(4, self.k * 2)
        
        # Temporarily override k if possible (some retrievers allow search_kwargs)
        if hasattr(self.vector_retriever, "search_kwargs"):
            old_vk = self.vector_retriever.search_kwargs.get("k", self.k)
            self.vector_retriever.search_kwargs["k"] = query_k
        
        if hasattr(self.bm25_retriever, "k"):
            old_bk = self.bm25_retriever.k
            self.bm25_retriever.k = query_k

        try:
            vector_docs = self.vector_retriever.invoke(query)
            bm25_docs = self.bm25_retriever.invoke(query)
        finally:
            # Restore k
            if hasattr(self.vector_retriever, "search_kwargs"):
                self.vector_retriever.search_kwargs["k"] = old_vk
            if hasattr(self.bm25_retriever, "k"):
                self.bm25_retriever.k = old_bk

        # 2. Merge & Deduplicate (Reciprocal Rank Fusion could be used, but simple interleaving works too)
        merged_children = []
        seen_child_ids = set()
        
        # Simple interleave
        for v_doc, b_doc in zip(vector_docs + [None]*len(bm25_docs), bm25_docs + [None]*len(vector_docs)):
            if v_doc:
                c_id = v_doc.metadata.get("chunk")
                if c_id not in seen_child_ids:
                    merged_children.append(v_doc)
                    seen_child_ids.add(c_id)
            if b_doc:
                c_id = b_doc.metadata.get("chunk")
                if c_id not in seen_child_ids:
                    merged_children.append(b_doc)
                    seen_child_ids.add(c_id)

        # 3. Get corresponding Parent Documents
        final_docs = []
        seen_parent_ids = set()
        
        for child_doc in merged_children:
            parent_id = child_doc.metadata.get("parent_id")
            if parent_id and parent_id not in seen_parent_ids:
                if parent_id in self.parent_store:
                    # Found parent doc
                    parent_doc = self.parent_store[parent_id]
                    # Pass the child info for citations
                    parent_doc.metadata["retrieved_via_child"] = child_doc.metadata.get("chunk")
                    final_docs.append(parent_doc)
                    seen_parent_ids.add(parent_id)
            
            if len(final_docs) >= self.k:
                break
                
        # Fallback if no parents (shouldn't happen with proper pipeline)
        if not final_docs:
            final_docs = merged_children[:self.k]

        return final_docs

def build_bm25_retriever(child_chunks: List[Document]) -> BM25Retriever:
    """Builds the BM25 keyword search retriever."""
    if not child_chunks:
        raise ValueError("Cannot build BM25 with empty chunks.")
    logger.info("Building BM25 Retriever from %d chunks...", len(child_chunks))
    retriever = BM25Retriever.from_documents(child_chunks)
    return retriever

def build_hybrid_retriever(
    vector_retriever: BaseRetriever, 
    bm25_retriever: BaseRetriever, 
    parent_docs: List[Document],
    k: int = 4
) -> AdvancedHybridRetriever:
    """Builds the advanced hybrid retriever combining Vector, BM25, and Parent mapping."""
    logger.info("Building Hybrid Retriever with Parent Mapping.")
    parent_store = {doc.metadata.get("parent_id"): doc for doc in parent_docs if "parent_id" in doc.metadata}
    
    return AdvancedHybridRetriever(
        vector_retriever=vector_retriever,
        bm25_retriever=bm25_retriever,
        parent_store=parent_store,
        k=k
    )
