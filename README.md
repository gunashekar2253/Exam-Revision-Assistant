# AI Study Assistant

A multi-agent AI backend + React frontend that turns uploaded documents into interactive **quizzes**, **flashcards**, and **study reviews** using RAG (Retrieval-Augmented Generation).



## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      React Frontend                         │
│  Upload docs │ Ask questions │ View quiz/flashcards/review  │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP (REST)
┌──────────────────────────▼──────────────────────────────────┐
│                    FastAPI Backend                          │
│                                                             │
│  ┌───────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │  /upload  │    │  /query      │    │ /reset-session   │  │
│  └─────┬─────┘    └──────┬───────┘    └──────────────────┘  │
│        │                 │                                  │
│  ┌─────▼─────┐    ┌──────▼───────┐                          │
│  │ Ingestion  │    │ Orchestrator  │                        │
│  │ Pipeline   │    │ (LLM Intent)  │                        │
│  │            │    └──────┬───────┘                         │
│  │ Extract    │           │                                 │
│  │ Chunk      │    ┌──────▼───────┐                         │
│  │ Embed      │    │  Task Agents  │                        │
│  │ Index      │    │ Quiz│Flash│Rev│                        │
│  └─────┬─────┘    └──────┬───────┘                          │
│        │                 │                                  │
│  ┌─────▼─────────────────▼───────┐   ┌──────────────────┐   │
│  │     FAISS Vector Store        │   │   LLM Router     │   │
│  │   (per-session isolation)     │   │ Groq → OpenRou   │   │
│  └───────────────────────────────┘   └──────────────────┘   │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Gemini API (Embeddings)                   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer         | Technology                    | Purpose                              |
|---------------|-------------------------------|--------------------------------------|
| **Frontend**  | React + Vite                  | UI for upload, query, and results    |
| **Backend**   | FastAPI + Uvicorn             | REST API and request handling        |
| **Embeddings**| Google Gemini API             | Text → vector embeddings             |
| **Vector DB** | FAISS (in-memory + disk)      | Similarity search for RAG retrieval  |
| **LLM**       | Groq (primary)                | Fast inference (Llama 3.3 70B)       |
| **LLM Fallback** | OpenRouter                 | Automatic fallback if Groq fails     |
| **Doc Parsing**| PyMuPDF, python-docx         | PDF and DOCX text extraction         |
| **Chunking**  | LangChain Text Splitters      | Recursive character-based splitting  |

---

## Project Structure

```
ai-mini/
├── backend/
│   ├── main.py                     # FastAPI app entry point
│   ├── requirements.txt            # Python dependencies
│   ├── .env                        # API keys & config (DO NOT COMMIT)
│   ├── .env.example                # Template for .env
│   │
│   ├── api/
│   │   └── routes.py               # All REST endpoints
│   │
│   ├── agents/
│   │   ├── base_agent.py           # Shared agent logic (RAG → LLM → Parse)
│   │   ├── orchestrator.py         # Intent classification + agent dispatch
│   │   └── task/
│   │       ├── quiz_agent.py       # MCQ generation agent
│   │       ├── flash_agent.py      # Flashcard generation agent
│   │       └── review_agent.py     # Summary/study plan agent
│   │
│   ├── core/
│   │   ├── config.py               # Centralized settings (env + paths)
│   │   ├── schema.py               # Pydantic request/response models
│   │   └── state.py                # In-memory session state tracking
│   │
│   ├── services/
│   │   └── ingestion/
│   │       ├── loader.py           # Multi-format text extraction
│   │       ├── chunker.py          # Text → chunks (500 chars, 50 overlap)
│   │       ├── embedder.py         # Chunks → vectors via Gemini API
│   │       └── indexer.py          # FAISS index (build, search, persist)
│   │
│   ├── tools/
│   │   ├── llm_router.py          # Groq + OpenRouter with failover
│   │   └── rag_tool.py            # Context retrieval from FAISS
│   │
│   ├── prompts/
│   │   ├── quiz_prompt.txt         # Quiz generation template
│   │   ├── flash_prompt.txt        # Flashcard generation template
│   │   └── review_prompt.txt       # Review/summary template
│   │
│   └── data/
│       └── sessions/               # Per-session storage (auto-created)
│           └── {session_id}/
│               ├── index/           # faiss.index + chunks.json
│               └── uploads/         # Raw uploaded files
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   └── src/
│       ├── main.jsx                # React entry point
│       ├── App.jsx                 # Main app component
│       ├── App.css                 # All styles
│       ├── api.js                  # Backend API helpers
│       └── components/
│           ├── FileUpload.jsx      # Drag-and-drop file upload
│           ├── QueryInput.jsx      # Query input + quick action hints
│           ├── QuizView.jsx        # Interactive MCQ quiz
│           ├── FlashcardView.jsx   # Flip-card flashcards
│           └── ReviewView.jsx      # Summary + study plan display
│
└── README.md
```

---

## Setup & Installation

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** and npm
- API keys for:
  - [Groq](https://console.groq.com/) (free tier available)
  - [Google Gemini](https://aistudio.google.com/apikey) (free tier: 100 embed requests/min)
  - [OpenRouter](https://openrouter.ai/) (optional fallback)

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd ai-mini
```

### 2. Backend setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend setup

```bash
cd frontend
npm install
```

---

## Configuration

Copy the example env file and fill in your API keys:

```bash
cd backend
cp .env.example .env
```

Edit `backend/.env`:

```env
# === LLM Provider Keys ===
GROQ_API_KEY=your_groq_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here    # Optional
GEMINI_API_KEY=your_gemini_api_key_here

# === Model Configuration ===
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_FAST_MODEL=llama-3.1-8b-instant
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct

# === Embedding Configuration ===
EMBEDDING_MODEL=gemini-embedding-001

# === Chunking Configuration ===
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# === RAG Configuration ===
RAG_TOP_K=5
```

### Key Configuration Notes

| Setting | Default | Description |
|---------|---------|-------------|
| `CHUNK_SIZE` | 500 | Characters per text chunk. Larger = more context per chunk |
| `CHUNK_OVERLAP` | 50 | Overlap between consecutive chunks to avoid cutting sentences |
| `RAG_TOP_K` | 5 | Number of most relevant chunks retrieved for each query |

---

## Running the Application

### Start the backend (Terminal 1)

```bash
cd backend
.\venv\Scripts\activate       # Windows
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Backend runs at: **http://localhost:8000**  
API docs at: **http://localhost:8000/docs**

### Start the frontend (Terminal 2)

```bash
cd frontend
npm run dev
```

Frontend runs at: **http://localhost:5173**

---

## API Reference

### `POST /api/upload`

Upload a document to create or append to a session.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | PDF, DOCX, TXT, MD, CSV, etc. |
| `session_id` | string | No | Existing session ID. If empty, a new session is auto-created. |

**Response:**
```json
{
  "message": "Successfully processed 'notes.pdf'",
  "filename": "notes.pdf",
  "num_chunks": 42,
  "num_characters": 21500,
  "session_id": "a3f8c2d1-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

### `POST /api/query`

Send a study query. The orchestrator auto-classifies intent and routes to the correct agent.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Your question (min 3 chars) |
| `session_id` | string | Yes | Session ID from upload |

**Response:**
```json
{
  "success": true,
  "type": "quiz",
  "intent": "quiz",
  "query": "Quiz me on machine learning",
  "session_id": "a3f8c2d1-...",
  "data": {
    "type": "quiz",
    "questions": [
      {
        "question": "What is supervised learning?",
        "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
        "correct_answer": "A",
        "explanation": "...",
        "difficulty": "medium"
      }
    ]
  }
}
```

### `POST /api/reset-session`

Clear all data (index, uploads, history) for a session.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | Yes | Session to reset |

### `GET /api/health?session_id=default`

Health check with index stats for a session.

### `GET /api/supported-formats`

Returns list of supported file extensions.

---

## How It Works

### 1. Document Ingestion Pipeline

```
Upload File → Extract Text → Chunk → Embed (Gemini) → Index (FAISS)
```

| Step | Module | Details |
|------|--------|---------|
| **Extract** | `loader.py` | PyMuPDF for PDF, python-docx for DOCX, plain read for TXT |
| **Chunk** | `chunker.py` | Recursive character splitter (500 chars, 50 overlap) |
| **Embed** | `embedder.py` | Gemini `gemini-embedding-001` with `RETRIEVAL_DOCUMENT` task type |
| **Index** | `indexer.py` | FAISS `IndexFlatIP` (inner product ≈ cosine similarity) |

### 2. Query Pipeline

```
User Query → Orchestrator (LLM classifies intent)
           → Task Agent (quiz/flashcard/review)
           → RAG Tool (embed query → FAISS search → top-K chunks)
           → LLM (generate response with retrieved context)
           → Parse JSON → Return to frontend
```

| Step | Module | Details |
|------|--------|---------|
| **Classify** | `orchestrator.py` | Fast LLM call (8B model) to detect intent |
| **Retrieve** | `rag_tool.py` | Embeds query with `RETRIEVAL_QUERY`, searches FAISS |
| **Generate** | `base_agent.py` | Fills prompt template with context + query, calls LLM |
| **Parse** | `base_agent.py` | Strips markdown code blocks, parses JSON |

### 3. Agent Types

| Agent | Intent Keywords | Output |
|-------|----------------|--------|
| **Quiz Agent** | "quiz", "test", "mcq", "questions" | MCQs with options, answers, explanations |
| **Flashcard Agent** | "flashcard", "cards", "memory" | Front/back pairs with categories |
| **Review Agent** | "summary", "review", "study plan", "key points" | Summary, key points, study plan, exam topics |

---

## Session Management

Sessions provide **data isolation** — each session has its own FAISS index and uploaded files.

### Lifecycle

```
1. First Upload (no session_id)
   → Backend auto-generates UUID
   → Returns session_id to frontend
   → Frontend stores it in localStorage

2. Subsequent Uploads (same session_id)
   → Documents APPEND to the existing index
   → Multiple docs build a richer knowledge base

3. Queries (same session_id)
   → Search only THIS session's index

4. Reset Session
   → Clears index + uploads + history
   → Frontend drops session_id
   → Next upload creates a fresh session
```

### Storage Layout

```
data/sessions/
├── a3f8c2d1-.../
│   ├── index/
│   │   ├── faiss.index    # Vector index
│   │   └── chunks.json    # Original text chunks
│   └── uploads/
│       ├── notes.pdf
│       └── chapter2.docx
└── b7e9f4a2-.../
    ├── index/...
    └── uploads/...
```

---

## Error Handling & Fallbacks

### LLM Failover

```
User Query → Groq (primary, fast)
             ↓ fails?
             → Retry 3x with exponential backoff (1s, 2s, 4s)
             ↓ still fails?
             → OpenRouter (fallback)
             ↓ both fail?
             → 503 Service Unavailable
```

### Embedding Rate Limits (Gemini Free Tier)

- Free tier: **100 requests/minute**
- Batch size: **20 chunks per request** (avoids exhausting quota in 1 call)
- Inter-batch delay: **1.5 seconds**
- On 429 error: retries with **10s → 30s → 45s → 60s** waits (up to 5 retries)
- Progress is **not lost** — only the failed batch retries

### Other Safeguards

| Scenario | Behavior |
|----------|----------|
| Duplicate filename upload | Rejected with 409 (prevents duplicate chunks in index) |
| Concurrent requests | Thread-safe FAISS cache with `threading.Lock` |
| Whitespace-only query | Stripped and rejected if < 3 real characters |
| Unrecognized intent | Falls back to "review" agent |
| Invalid JSON from LLM | Returns `raw_response` with parse error instead of crashing |
| Scanned PDF (no text) | Returns 400 with clear error message |
| No documents uploaded | Returns 503: "Please upload a document first" |

---

## Supported File Formats

| Format | Extension | Parser |
|--------|-----------|--------|
| PDF | `.pdf` | PyMuPDF |
| Word | `.docx` | python-docx |
| Plain Text | `.txt` | Built-in |
| Markdown | `.md` | Built-in |
| CSV | `.csv` | Built-in |
| JSON | `.json` | Built-in |
| XML | `.xml` | Built-in |
| HTML | `.html` | Built-in |
| Python | `.py` | Built-in |
| Log files | `.log` | Built-in |

---


