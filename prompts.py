"""
prompts.py — Production-Quality Prompt Templates
==================================================
All PromptTemplate definitions live here.

Design principles:
    - Every prompt is specific, structured, and output-constrained.
    - Generic prompts ("summarize this") are avoided; each prompt
      instructs the model on format, length, and style.
    - summary_prompt operates on the RAW DOCUMENT (legacy / graph.py).
    - map_prompt operates on a SINGLE CHUNK (Map-Reduce Step 1).
    - reduce_prompt merges PARTIAL SUMMARIES (Map-Reduce Step 2).
    - All downstream prompts (key_points, quiz, flashcard) operate on
      the SUMMARY — significantly reducing token usage.
    - Adding a new chain = adding one PromptTemplate here + one chain
      in chains.py.  No other files change.

Token strategy (Map-Reduce architecture):
    map_prompt          → input: one chunk (~800 chars) | output: ~60 tokens
    reduce_prompt       → input: N partial summaries    | output: ~200 tokens
    keypoints_prompt    → input: summary (~200t)         | output: ~150 tokens
    quiz_prompt         → input: summary (~200t)         | output: ~300 tokens
    flashcard_prompt    → input: summary (~200t)         | output: ~200 tokens

    Net saving vs. single-pass (full doc sent to LLM once):
        Map-Reduce: N × chunk_tokens + 1 × partial_summary_tokens
        Chunks are ~800 chars each — far smaller than a full document.
        The reduce step receives only ~60-token stubs, not the raw text.
"""

from langchain_core.prompts import PromptTemplate

from langchain_core.prompts import PromptTemplate

# ---------------------------------------------------------------------------
# 1. Map Prompt (input: {chunk})
# ---------------------------------------------------------------------------
map_prompt = PromptTemplate.from_template(
    """<start_of_turn>user
Summarize in 2-3 concise, factual sentences. Avoid repetition.
Text: {chunk}
<end_of_turn>
<start_of_turn>model
"""
)

# ---------------------------------------------------------------------------
# 2. Reduce Prompt (input: {summaries})
# ---------------------------------------------------------------------------
reduce_prompt = PromptTemplate.from_template(
    """<start_of_turn>user
Merge these summaries into one coherent summary of exactly 5 sentences. Use academic style.
Summaries:
{summaries}
<end_of_turn>
<start_of_turn>model
"""
)

# ---------------------------------------------------------------------------
# 3. Summary Prompt (input: {document}) — legacy
# ---------------------------------------------------------------------------
summary_prompt = PromptTemplate.from_template(
    """<start_of_turn>user
Summarize this text in exactly 5 concise, information-dense sentences:
{document}
<end_of_turn>
<start_of_turn>model
"""
)

# ---------------------------------------------------------------------------
# 4. Key Points Prompt (input: {summary})
# ---------------------------------------------------------------------------
keypoints_prompt = PromptTemplate.from_template(
    """<start_of_turn>user
Based on the summary, extract 5 key concepts as a numbered list (1. 2. 3. 4. 5.). Format each as a single self-contained sentence.
Summary:
{summary}
<end_of_turn>
<start_of_turn>model
"""
)

# ---------------------------------------------------------------------------
# 5. Quiz Prompt (input: {summary})
# ---------------------------------------------------------------------------
quiz_prompt = PromptTemplate.from_template(
    """<start_of_turn>user
Based on the summary, generate exactly 5 quiz questions with short answers (1-2 sentences). Use this format:
Q1: <question>
A1: <answer>
... through Q5/A5. Do not include multiple-choice options.
Summary:
{summary}
<end_of_turn>
<start_of_turn>model
"""
)

# ---------------------------------------------------------------------------
# 6. Flashcard Prompt (input: {summary})
# ---------------------------------------------------------------------------
flashcard_prompt = PromptTemplate.from_template(
    """<start_of_turn>user
Based on the summary, generate exactly 5 term/definition flashcards. Use this format:
Card 1:
Q: <term>
A: <crisp definition>
... through Card 5.
Summary:
{summary}
<end_of_turn>
<start_of_turn>model
"""
)

# ---------------------------------------------------------------------------
# 7. AI Insights Prompt (input: {summary}) — legacy, kept for backward compat
# ---------------------------------------------------------------------------
ai_insights_prompt = PromptTemplate.from_template(
    """<start_of_turn>user
Analyze this summary and output exactly in this format:
Topic: <main topic, max 5 words>
Difficulty: <Easy, Medium, or Hard>
Concepts: <exactly 3 key terms, comma-separated>

Summary:
{summary}
<end_of_turn>
<start_of_turn>model
"""
)

study_material_prompt = PromptTemplate.from_template(
    """<start_of_turn>user
You are a study material generator. Using ONLY the text below, generate ALL study materials as a single valid JSON object. Do NOT include any text outside the JSON.

Text:
{text}

Generate exactly this JSON structure:
{{
  "summary": "<Generate a concise summary of maximum 250 words>",
  "key_points": ["point1", "point2", "point3", "point4", "point5", "point6", "point7", "point8", "point9", "point10"],
  "quiz": {{
    "mcq": [
      {{"question": "", "options": ["A", "B", "C", "D"], "answer": ""}}
      // Generate exactly 10 MCQs
    ]
  }},
  "flashcards": [
    {{"front": "", "back": ""}}
    // Generate exactly 10 flashcards
  ],
  "ai_insights": [
    "insight1", "insight2", "insight3", "insight4", "insight5"
  ]
}}

Rules:
- 1 summary (maximum 250 words)
- 10 key points as short bullets
- 10 MCQs with 4 options each and correct answer
- 10 flashcards with front (term/question) and back (definition/answer)
- 5 AI insights (interesting facts or connections)
- Return ONLY valid JSON, no markdown, no explanation
<end_of_turn>
<start_of_turn>model
"""
)

# ---------------------------------------------------------------------------
# 8. Mind Map Prompt (input: {summary})
# ---------------------------------------------------------------------------
mindmap_prompt = PromptTemplate.from_template(
    """<start_of_turn>user
You are a Mermaid.js expert. Based ONLY on the following summary, generate a Mermaid.js diagram code that represents a Mind Map of the core concepts.

Rules:
1. Output ONLY valid Mermaid syntax.
2. Do NOT wrap the output in markdown backticks (e.g. ```mermaid).
3. Do NOT include any explanations, JSON, or surrounding text.
4. Prefer 'mindmap' syntax (e.g. 'mindmap\n  root((Concept))\n    Child1\n    Child2'). If not possible, use 'graph TD'.
5. Create a clear hierarchy with parent-child relationships.
6. Maximum 40 nodes.
7. No duplicate nodes.

Summary:
{summary}
<end_of_turn>
<start_of_turn>model
"""
)

# ---------------------------------------------------------------------------
# 9. Exam Generator Prompt (input: {summary}, {key_points}, {marks}, {bloom_level}, {count})
# ---------------------------------------------------------------------------
exam_generator_prompt = PromptTemplate.from_template(
    """<start_of_turn>user
You are a Senior University Professor. Generate EXACTLY {count} exam questions based on the following content.

Settings:
- Marks per question: {marks}
- Bloom's Taxonomy Level: {bloom_level}
- Target length for model answers: 
  - 2 Marks: 40-60 words
  - 5 Marks: 120-180 words
  - 10 Marks: 250-350 words

Generate exactly this JSON structure:
{{
  "questions": [
    {{
      "question": "<The question text>",
      "marks": "{marks}",
      "taxonomy": "{bloom_level}",
      "answer": "<The comprehensive model answer>",
      "keywords": ["keyword1", "keyword2", "keyword3"],
      "difficulty": "<Easy, Medium, or Hard>"
    }}
  ]
}}

Rules:
- The questions MUST match the specified Bloom's Taxonomy level.
- The model answer MUST be detailed and educational, matching the target length for {marks} marks.
- Return ONLY valid JSON, no markdown, no explanation.

Content Summary:
{summary}

Key Points:
{key_points}
<end_of_turn>
<start_of_turn>model
"""
)
