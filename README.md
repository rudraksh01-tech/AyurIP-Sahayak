# 🌿 AyurIP-Sahayak

## AI Assistant for Ayurveda, Traditional Knowledge & Intellectual Property Rights

**AyurIP-Sahayak** is an AI-powered research assistant that helps users explore **Ayurveda, Traditional Knowledge, TKDL, and Intellectual Property Rights (IPR)** using a Retrieval-Augmented Generation (RAG) pipeline.

The system retrieves relevant information from a curated knowledge base and uses an AI model to generate clear, contextual answers.

---

## 🚀 Features

* 🔎 Semantic search over Ayurveda and IPR documents
* 🤖 AI-powered question answering
* 📚 Source-aware responses
* 🌿 Ayurveda and Traditional Knowledge focused knowledge base
* ⚖️ Intellectual Property Rights (IPR) research support
* 📖 TKDL-related information
* ⚡ FastAPI backend
* 💻 React + Vite frontend
* 🔗 Retrieval-Augmented Generation (RAG) architecture
* 🔐 API keys managed using environment variables

---

## 🧠 How It Works

AyurIP-Sahayak follows a **RAG (Retrieval-Augmented Generation)** approach.

```text
User Question
      ↓
Question Processing
      ↓
Semantic Retrieval
      ↓
Relevant Knowledge Chunks
      ↓
AI Generation
      ↓
Answer + Sources
```

Instead of asking the AI to answer only from its general knowledge, the system first retrieves relevant information from the project's knowledge base.

This helps produce answers that are more relevant to the provided Ayurveda, Traditional Knowledge, and IPR documents.

---

## 🏗️ Architecture

```text
                  ┌──────────────────┐
                  │      User        │
                  └────────┬─────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │ React + Vite UI  │
                  └────────┬─────────┘
                           │ HTTP
                           ▼
                  ┌──────────────────┐
                  │ FastAPI Backend  │
                  └────────┬─────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │   RAG Pipeline   │
                  └───────┬───┬──────┘
                          │   │
             ┌────────────┘   └────────────┐
             ▼                             ▼
      ┌──────────────┐              ┌──────────────┐
      │  Retrieval   │              │ AI Generation│
      └──────┬───────┘              └──────┬───────┘
             │                             │
             ▼                             ▼
      Knowledge Base                Generated Answer
             │                             │
             └─────────────┬───────────────┘
                           ▼
                    Answer + Sources
```

---

## 🛠️ Technology Stack

### Frontend

* React
* Vite
* JavaScript
* CSS

### Backend

* Python
* FastAPI
* Uvicorn

### RAG / AI

* Retrieval-Augmented Generation
* Sentence Transformers
* `all-MiniLM-L6-v2`
* Vector embeddings
* Semantic similarity search
* Google Gemini API

### Data

* PDF/document-based knowledge
* Processed text chunks
* Embedding-based retrieval

---

## 📂 Project Structure

```text
AyurIP-Sahayak/
│
├── backend/
│   ├── app/
│   │   └── main.py
│   │
│   ├── rag/
│   │   ├── ingestion/
│   │   ├── retrieval/
│   │   ├── generation/
│   │   └── rag_pipeline.py
│   │
│   ├── data/
│   │   ├── raw/
│   │   └── processed/
│   │
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   │
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
├── docs/
│
├── .gitignore
└── README.md
```

---

## ⚙️ Setup

### 1. Clone the repository

```bash
git clone https://github.com/rudraksh01-tech/AyurIP-Sahayak.git
cd AyurIP-Sahayak
```

---

## 🐍 Backend Setup

Create and activate a virtual environment:

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
cd backend
pip install -r requirements.txt
```

Create a `.env` file inside `backend/` and add your API configuration.

Example:

```env
GEMINI_API_KEY=your_api_key_here
```

**Never commit your real API key to GitHub.**

Start the backend:

```powershell
uvicorn app.main:app --reload
```

Backend will normally be available at:

```text
http://127.0.0.1:8000
```

---

## 💻 Frontend Setup

Open another terminal:

```powershell
cd D:\Projects\AyurIP-Sahayak\frontend
npm install
npm run dev
```

The Vite development server will provide a local URL such as:

```text
http://localhost:5173/
```

Open that URL in your browser.

---

## 💬 Example Questions

You can ask questions such as:

* What is TKDL?
* What is Traditional Knowledge?
* What is defensive protection of traditional knowledge?
* How does traditional knowledge affect patents?
* What is the relationship between Ayurveda and IPR?
* How can traditional knowledge be protected?

---

## 🔄 RAG Pipeline

The project follows these major stages:

### 1. Document Ingestion

Source documents are collected and processed.

### 2. Text Extraction

Useful text is extracted from the documents.

### 3. Chunking

Large documents are divided into smaller meaningful chunks.

### 4. Embedding Generation

Each chunk is converted into a numerical vector using:

```text
all-MiniLM-L6-v2
```

### 5. Retrieval

When a user asks a question, the system converts the question into an embedding and compares it with stored document embeddings.

The most relevant chunks are selected.

### 6. Generation

The retrieved information is passed to the AI generation layer to produce the final answer.

### 7. Sources

Relevant retrieved documents/chunks are displayed along with the generated answer.

---

## 🎯 Project Goal

The goal of AyurIP-Sahayak is to make research around **Ayurveda, Traditional Knowledge, TKDL, and Intellectual Property Rights** easier and more accessible through an AI-assisted interface.

The project demonstrates how modern **RAG architecture** can be applied to domain-specific research.

---

## 🔒 Security

Sensitive configuration such as API keys should be stored in environment variables.

The repository ignores environment files using `.gitignore`.

```text
.env
.env.*
!.env.example
```

Do not upload API keys, passwords, or other secrets to GitHub.

---

## 🚧 Current Status

**Working prototype**

The current version includes:

* ✅ React frontend
* ✅ FastAPI backend
* ✅ RAG pipeline
* ✅ Semantic retrieval
* ✅ Embedding-based search
* ✅ Gemini API integration
* ✅ Source display
* ✅ Local frontend/backend integration
* ✅ GitHub repository

---

## 🔮 Future Improvements

* 🌐 Hindi and multilingual question answering
* 📊 Better retrieval evaluation
* 🔍 Improved citation and source display
* 📚 Larger government/document knowledge base
* ☁️ Production deployment
* 🔐 Authentication and user management
* 📈 RAG evaluation metrics
* 🗂️ Better document management
* 💾 Conversation history

---

## 👨‍💻 Author

**Rudra Pratap Singh**

AyurIP-Sahayak is developed as an AI/RAG project focused on applying Generative AI to Ayurveda, Traditional Knowledge, and Intellectual Property research.

---

## 📄 License

This project is intended for educational and research purposes.
