"""
rag/splitter.py — Document Text Splitter for Parent-Child
=========================================================
Provides splitters and utility to split a document into 
parent and child chunks for advanced retrieval.
"""

from __future__ import annotations

import logging
import uuid
from typing import Tuple

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

# Separator priority
_SEPARATORS: list[str] = ["\n\n", "\n", ". ", " ", ""]

def get_parent_splitter() -> RecursiveCharacterTextSplitter:
    """Creates the splitter for large parent chunks (1500-2000 chars)"""
    return RecursiveCharacterTextSplitter(
        chunk_size=1800,
        chunk_overlap=200,
        separators=_SEPARATORS,
        length_function=len,
        add_start_index=True,
    )

def get_child_splitter() -> RecursiveCharacterTextSplitter:
    """Creates the splitter for small child chunks (300-500 chars)"""
    return RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=50,
        separators=_SEPARATORS,
        length_function=len,
        add_start_index=True,
    )

def split_document(text: str) -> Tuple[list[Document], list[Document]]:
    """
    Splits text into Parent and Child chunks, manually linking them via metadata.
    Returns (parent_docs, child_docs).
    """
    if not text or not text.strip():
        raise ValueError("Cannot split an empty document.")

    parent_splitter = get_parent_splitter()
    child_splitter = get_child_splitter()

    parent_docs = parent_splitter.create_documents([text])
    child_docs = []

    child_idx_global = 0
    
    for i, p_doc in enumerate(parent_docs):
        # Assign unique ID to parent
        parent_id = str(uuid.uuid4())
        p_doc.metadata["parent_id"] = parent_id
        p_doc.metadata["chunk"] = i
        
        # Split this parent into children
        children = child_splitter.split_documents([p_doc])
        for c in children:
            c.metadata["parent_id"] = parent_id
            c.metadata["chunk"] = child_idx_global
            c.metadata["parent_chunk"] = i
            child_idx_global += 1
            child_docs.append(c)

    logger.info(
        "Document split into %d Parent chunks and %d Child chunks.",
        len(parent_docs),
        len(child_docs)
    )

    return parent_docs, child_docs
