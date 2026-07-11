# 📚 Smart Study Assistant

An AI-powered document analysis application built using **LangChain**, **RunnableParallel**, **TinyLlama**, and **Streamlit**.

The application accepts a document or pasted text and simultaneously generates:

- 📄 Summary
- 📌 Key Points
- 📝 Quiz Questions
- 🧠 Flashcards

using **Parallel Chains** in LangChain.

---

## 🚀 Features

- Upload documents
  - ✅ TXT
  - ✅ PDF
  - ✅ DOCX
- Paste custom text
- AI-generated Summary
- AI-generated Key Points
- AI-generated Quiz
- AI-generated Flashcards
- Download Study Report
- Parallel execution using LangChain RunnableParallel

---

## 🛠 Tech Stack

- Python
- LangChain
- TinyLlama-1.1B-Chat
- HuggingFace
- Streamlit
- RunnableParallel
- PromptTemplate
- StrOutputParser
- PyPDF2
- python-docx

---

## 📂 Project Structure

```
Smart_Study_Assistant/
│
├── app.py                  # Streamlit application
├── chains.py               # LangChain Parallel Chain
├── requirements.txt
├── README.md
│
└── assets/
    ├── flow.png
    ├── study1.png
    ├── study2.png
    └── study3.png
```

---

## ⚙️ Workflow

```
Document
      │
      ▼
RunnableParallel
      │
 ├───────────────┐
 │               │
 ▼               ▼
Summary      Key Points

 ▼               ▼
Quiz        Flashcards
      │
      ▼
 Merge Output
      │
      ▼
 Streamlit UI
```

---

## 🧩 LangChain Graph

> Generated using `chain.get_graph().print_ascii()`

<img width="658" height="434" alt="flow" src="https://github.com/user-attachments/assets/8104fb82-ca18-4a40-8b3a-35b0dd5d0df5" />


---

## 📸 Application Preview

### Home Page

<img width="895" height="480" alt="study1" src="https://github.com/user-attachments/assets/8c83b077-7594-4849-8045-6e2af28c880b" />


---

### Summary

<img width="950" height="498" alt="study2" src="https://github.com/user-attachments/assets/f6926d54-92ff-4992-8f69-640461c6df4c" />


---

### Key Points

<img width="937" height="471" alt="study3" src="https://github.com/user-attachments/assets/42cb3c07-5e9d-4b8d-9f18-ce4761a789dc" />


---

## 🧠 Parallel Chain Architecture

Each task runs independently using **RunnableParallel**.

```
Input Document
      │
      ▼
RunnableParallel
│      │      │      │
▼      ▼      ▼      ▼
Summary
Key Points
Quiz
Flashcards
      │
      ▼
Merged Output
```

---

## ▶️ Installation

Clone the repository

```bash
git clone https://github.com/yourusername/Smart-Study-Assistant.git
```

Move inside the project

```bash
cd Smart-Study-Assistant
```

Create virtual environment

```bash
python -m venv venv
```

Activate environment

Windows

```bash
venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run Streamlit

```bash
streamlit run app.py
```

---

## 📦 Requirements

- Python 3.11+
- Streamlit
- LangChain
- LangChain-HuggingFace
- Transformers
- Torch
- PyPDF2
- python-docx

---

## 📖 Concepts Used

- PromptTemplate
- RunnableParallel
- RunnableLambda
- Chat Models
- StrOutputParser
- Sequential Workflow
- Parallel Execution
- HuggingFacePipeline
- Streamlit

---

## 🎯 Future Improvements

- Support larger documents using Text Splitters
- Retrieval-Augmented Generation (RAG)
- Vector Database Integration
- Conversation Memory
- PDF Export
- MCQ Answer Evaluation
- Multiple LLM Support (Gemma, Mistral, Llama)

---

## 👨‍💻 Author

**Omkar Narsale**

GitHub: https://github.com/Omkar-narsale

LinkedIn: www.linkedin.com/in/omkar-narsale45

---

⭐ If you found this project useful, consider giving it a Star!
