"""
rag/prompts.py — RAG Prompt Template
======================================
Defines the prompt used by the RAG chain to answer questions
grounded exclusively in the retrieved document context.

Design principles:
    - Strict grounding: the model is instructed to answer ONLY from context.
    - Graceful fallback: if information is absent, the model says so rather
      than hallucinating.
    - Minimal instructions: Gemma is an instruction-tuned model — concise,
      clear instructions outperform lengthy system prompts on CPU.

Variables:
    {context}  — Joined text of the top-k retrieved document chunks.
    {question} — The user's natural language question.

Separation of concerns:
    This file contains only RAG prompts.  The study pipeline prompts
    (summary, key_points, quiz, flashcard) remain in the top-level
    prompts.py and are completely unaffected.
"""

from langchain_core.prompts import PromptTemplate

# ---------------------------------------------------------------------------
# RAG Prompt  (input: {context}, {question})
# ---------------------------------------------------------------------------

RAG_PROMPT: PromptTemplate = PromptTemplate.from_template(
    """You are a helpful study assistant.
Answer ONLY using the supplied context.
If the answer is unavailable inside the document, respond that the information is not present in the provided material.

Context:
{context}

Question:
{question}

Answer:"""
)
