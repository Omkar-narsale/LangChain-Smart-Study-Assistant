# 📚 Smart Study Assistant Pro

> 🚀 An AI-powered study companion that transforms PDFs, DOCX, and TXT files into interactive learning experiences using **Retrieval-Augmented Generation (RAG)**, **Groq LLM**, **LangChain**, and **FAISS**.

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red?style=for-the-badge&logo=streamlit)
![LangChain](https://img.shields.io/badge/LangChain-RAG-green?style=for-the-badge)
![FAISS](https://img.shields.io/badge/FAISS-Vector%20Database-purple?style=for-the-badge)
![Groq](https://img.shields.io/badge/Groq-LLM-orange?style=for-the-badge)

---

## 🌟 Features

### 📄 Smart Document Processing
- 📂 Upload PDF, DOCX, and TXT files
- ✂ Intelligent text chunking
- 🧠 Semantic embeddings
- ⚡ Fast FAISS vector search
- 🔍 Retrieval-Augmented Generation (RAG)

### 🤖 AI Study Assistant
- 💬 Ask questions from your documents
- 📚 Source citations with page references
- 🎯 Confidence score for retrieved content
- 📄 Context-aware responses
- 🚫 Reduced hallucinations using RAG

### 📖 Study Tools
- 📝 AI Summary
- 🔑 Key Points
- 🎴 Flashcards
- ❓ Quiz Generator
- 🧠 Mind Map Generator
- 📊 AI Presentation Generator

### 🌍 Multilingual Support
- 🇺🇸 English
- 🇮🇳 Hindi
- 🇮🇳 Marathi

---

# 🏗️ System Architecture

```text
                    User Uploads Document
                            │
                            ▼
                 PDF / DOCX / TXT Loader
                            │
                            ▼
                 LangChain Document Objects
                            │
                            ▼
          RecursiveCharacterTextSplitter
                            │
                            ▼
                     Document Chunks
                            │
                            ▼
     HuggingFace Embeddings (MiniLM-L6-v2)
                            │
                            ▼
                 FAISS Vector Database
                            │
        ┌───────────────────┴───────────────────┐
        ▼                                       ▼
  Similarity Search                        Metadata
(Page, Source, Chunk)                  (Page Numbers)
        │
        ▼
      Retriever
        │
        ▼
 Prompt + Retrieved Context
        │
        ▼
      Groq LLM
        │
        ▼
 Summary │ Quiz │ Flashcards │ AI Chat │ Mind Map
```

---

# 🧠 How RAG Works

```text
User Uploads PDF
        │
        ▼
Document Loader
        │
        ▼
Text Splitter
        │
        ▼
Chunks
        │
        ▼
Embeddings
        │
        ▼
FAISS Vector Store
───────────────────────────────────────────
User asks Question
        │
        ▼
Question Embedding
        │
        ▼
Similarity Search
        │
        ▼
Top Relevant Chunks
        │
        ▼
Prompt Construction
        │
        ▼
Groq LLM
        │
        ▼
Answer + Citations + Confidence Score
```

---

# ⚙️ Tech Stack

| Category | Technology |
|-----------|------------|
| Frontend | Streamlit |
| Backend | Python |
| LLM | Groq |
| Framework | LangChain |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| Vector Database | FAISS |
| Document Loader | PyPDFLoader, Docx2txtLoader, TextLoader |
| Text Splitter | RecursiveCharacterTextSplitter |
| Presentation | python-pptx |
| Visualization | Plotly |

---

# 📚 Ask PDF with Citations

Unlike traditional chatbots, Smart Study Assistant Pro answers questions **only from the uploaded document**.

### Example

```text
🤖 Answer

Large Language Models predict the next token...

────────────────────────────

📚 Sources

✓ Page 5 (96%)

✓ Page 7 (92%)

✓ Page 9 (88%)

────────────────────────────

📊 Retrieval Statistics

Retrieved Chunks : 4

Average Confidence : 92%

Response Time : 1.1 sec
```

---

# 🚀 Installation

Clone the repository

```bash
git clone https://github.com/Omkar-narsale/Smart-Study-Assistant-Pro.git
```

Move into the project

```bash
cd Smart-Study-Assistant-Pro
```

Install dependencies

```bash
pip install -r requirements.txt
```

Create a `.env` file

```env
GROQ_API_KEY=your_groq_api_key
```

Run the application

```bash
streamlit run app.py
```

---

# 📂 Project Structure

```text
Smart-Study-Assistant-Pro
│
├── app.py
├── requirements.txt
├── .env
├── assets/
├── uploads/
├── vector_store/
├── embeddings/
├── pages/
├── utils/
├── generated/
└── README.md
```

---

# 🎯 Core Features

- ✅ Upload PDF, DOCX & TXT
- ✅ Semantic Search
- ✅ Retrieval-Augmented Generation (RAG)
- ✅ AI Chat
- ✅ AI Summary
- ✅ Flashcards
- ✅ Quiz Generator
- ✅ Mind Map
- ✅ AI Presentation Generator
- ✅ Source Citations
- ✅ Confidence Scores
- ✅ Cached Embeddings
- ✅ Fast Retrieval



# 🛣️ Future Improvements

- [ ] OCR Support
- [ ] Voice Assistant
- [ ] Multi-PDF Chat
- [ ] AI Notes Generator
- [ ] Image Understanding
- [ ] YouTube Summarizer
- [ ] Authentication
- [ ] Cloud Deployment

---

# 🤝 Contributing

Contributions are welcome!

1. Fork this repository
2. Create a new branch
3. Commit your changes
4. Push to your fork
5. Open a Pull Request

---

# 👨‍💻 Author

**Omkar Narsale**

- 💻 GitHub: https://github.com/Omkar-narsale
- 💼 LinkedIn:www.linkedin.com/in/omkar-narsale45

---

# ⭐ Support

If you found this project useful, consider giving it a **⭐ Star** on GitHub!

---

## Made with ❤️ using Python, Streamlit, LangChain, FAISS & Groq
