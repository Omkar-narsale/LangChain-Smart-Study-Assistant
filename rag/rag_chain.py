"""
rag/rag_chain.py — Advanced RAG LCEL Chain
==========================================
Implements Dynamic Retrieval (top-k scaling based on query complexity)
and Context Compression (removing irrelevant sentences).
"""

from __future__ import annotations

import logging
from typing import Any, List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import (
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
)
from langchain_core.documents import Document

from rag.prompts import RAG_PROMPT
from config import invoke_with_retry

logger = logging.getLogger(__name__)

_parser = StrOutputParser()


def _format_context(docs: List[Document]) -> str:
    """Format compressed chunks."""
    if not docs:
        return "No relevant context found in the document."

    parts: list[str] = []
    for i, doc in enumerate(docs):
        # We might have parent_id or retrieved_via_child
        chunk_id = doc.metadata.get("chunk", i)
        page_id = doc.metadata.get("page", "?")
        parts.append(f"[Source: Chunk {chunk_id} | Page {page_id}]\n{doc.page_content.strip()}")

    return "\n\n---\n\n".join(parts)


def build_rag_chain(retriever, llm) -> Any:
    """
    Build and return an advanced RAG LCEL chain.
    """
    logger.info("Building Advanced RAG chain...")

    def _dynamic_retrieve(question: str) -> List[Document]:
        # Simple dynamic retrieval depth heuristic based on question complexity
        word_count = len(question.split())
        
        # Adjust base retriever's k dynamically
        # Since it's our AdvancedHybridRetriever, it has a k property
        if hasattr(retriever, 'k'):
            if word_count < 6:
                retriever.k = 1
                logger.info("Dynamic Retrieval: Simple question -> k=1")
            elif word_count < 15:
                retriever.k = 2
                logger.info("Dynamic Retrieval: Medium question -> k=2")
            else:
                retriever.k = 4
                logger.info("Dynamic Retrieval: Complex question -> k=4")

        # Invoke with retry for reliability (using the base retriever)
        docs = invoke_with_retry(retriever, question)
        return docs

    # ── Step 1: Retrieve docs AND pass the question through simultaneously ──
    retrieve_and_passthrough = RunnableParallel(
        docs=RunnableLambda(_dynamic_retrieve),
        question=RunnablePassthrough(),
    )

    # ── Step 2: Format the retrieved docs into a context string ──
    format_step = RunnableLambda(
        lambda x: {
            "context": _format_context(x["docs"]),
            "question": x["question"],
            "sources": x["docs"],
        }
    )

    # ── Step 3: Generate the answer from context + question ──
    # Note: For streaming, we don't invoke it entirely here if we want to stream tokens to the UI.
    # We return the pieces so the UI can call `.stream()` or `.invoke()` directly on the pipeline.
    # However, LCEL streams naturally if the last step is an LLM.
    def _generate_answer(inputs: dict) -> dict:
        answer_stream_chain = RAG_PROMPT | llm | _parser
        # We just store the chain runnable here so the caller can stream it
        # Actually, returning the invoked result breaks streaming if we don't yield.
        # But wait, the previous code just did `.invoke()`.
        # To support streaming, we need to return the generator or just let the user call `.stream()` on the full chain.
        # But `sources` needs to be yielded too.
        # A common pattern is to return `docs` and let the UI stream the LLM.
        return inputs # Passing inputs down, let the caller handle generation to support streaming cleanly.

    def _final_generation(inputs: dict) -> Any:
        return {
            "answer": invoke_with_retry((RAG_PROMPT | llm | _parser), {"context": inputs["context"], "question": inputs["question"]}),
            "sources": inputs["sources"]
        }
    
    # We will build it so `.invoke()` works normally, but we'll also expose a way to stream in the UI.
    rag_chain = retrieve_and_passthrough | format_step | RunnableLambda(_final_generation)

    logger.info("Advanced RAG chain built successfully.")
    return rag_chain
