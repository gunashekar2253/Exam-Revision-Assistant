# AI Study Assistant — Backend Implementation Plan

## Goal

Build a modular, production-grade AI backend that powers an intelligent study assistant. The system ingests PDFs, stores them as vector embeddings (FAISS), and orchestrates multiple specialized agents (Quiz, Flashcard, Review) via an LLM to generate study content grounded in the user's uploaded material.

---

## Technology Stack

| Layer | Choice | Rationale |
|---|---|---|
| **Framework** | FastAPI | Async, auto-docs, Pydantic native |
| **PDF Extraction** | PyMuPDF (`fitz`) | Fastest extraction, layout-aware, handles complex PDFs |
| **Chunking** | `RecursiveCharacterTextSplitter` (LangChain) | Semantic-aware splitting, preserves context boundaries |
| **Embeddings** | `sentence-transformers` (`all-MiniLM-L6-v2`) | Fast, lightweight, excellent for RAG |
| **Vector Store** | FAISS (`faiss-cpu`) | In-memory, fast similarity search, no external DB needed |
| **LLM (Primary)** | Groq API (`llama-3.3-70b-versatile`) | Free tier, ultra-fast inference |
| **LLM (Fallback)** | OpenRouter API | Fallback when Groq rate-limited |
| **Data Models** | Pydantic v2 | Schema validation, serialization |
| **Storage** | JSON files (local) | Simple MCP-style result persistence |

---

## Proposed Changes

### Build Order

We follow your specified build order strictly:

```
Phase 1 → PDF ingestion + FAISS (services/ingestion/*)
Phase 2 → RAG tool (tools/rag_tool.py)
Phase 3 → One agent — Quiz (agents/task/quiz_agent.py)
Phase 4 → API layer (/upload + /query)
Phase 5 → Orchestrator (agents/orchestrator.py)
Phase 6 → Add Flashcard + Review agents
Phase 7 → MCP saving (tools/mcp_tool.py)
Phase 8 → LLM routing (tools/llm_router.py)
```

---

### Final Folder Structure

```text
backend/
├── main.py                          # FastAPI entry point
├── requirements.txt                 # All dependencies
├── .env.example                     # Template for API keys
│
├── api/
│   ├── __init__.py
│   └── routes.py                    # /upload, /query, /health endpoints
│
├── agents/
│   ├── __init__.py
│   ├── base_agent.py                # Shared agent logic (context retrieval)
│   ├── orchestrator.py              # Intent classification → agent dispatch
│   ├── evaluator_agent.py           # Optional: validate/score LLM output
│   └── task/
│       ├── __init__.py
│       ├── quiz_agent.py            # Generate MCQs from context
│       ├── flash_agent.py           # Generate flashcards from context
│       └── review_agent.py          # Summaries, key points, study plans
│
├── services/
│   ├── __init__.py
│   └── ingestion/
│       ├── __init__.py
│       ├── loader.py                # PDF → raw text (PyMuPDF)
│       ├── chunker.py               # Text → semantic chunks
│       ├── embedder.py              # Chunks → vector embeddings
│       └── indexer.py               # Embeddings → FAISS index
│
├── tools/
│   ├── __init__.py
│   ├── rag_tool.py                  # Query FAISS → return relevant chunks
│   ├── llm_router.py               # LLM provider selection + retry logic
│   └── mcp_tool.py                  # Save/load results to JSON
│
├── prompts/
│   ├── quiz_prompt.txt              # Quiz generation prompt template
│   ├── flash_prompt.txt             # Flashcard generation prompt template
│   └── review_prompt.txt            # Review/summary prompt template
│
├── core/
│   ├── __init__.py
│   ├── config.py                    # Settings via pydantic-settings + .env
│   ├── schema.py                    # Pydantic request/response models
│   └── state.py                     # In-memory session state (history, progress)
│
└── data/
    ├── uploads/                     # Raw uploaded PDFs
    ├── index/                       # Persisted FAISS index files
    └── results/                     # MCP-saved JSON results
```

---

### Phase 1 — PDF Ingestion + FAISS

#### [NEW] `requirements.txt`

```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
python-multipart>=0.0.9
pydantic>=2.0
pydantic-settings>=2.0
pymupdf>=1.24.0
langchain-text-splitters>=0.2.0
sentence-transformers>=3.0.0
faiss-cpu>=1.8.0
numpy>=1.26.0
groq>=0.9.0
openai>=1.40.0
python-dotenv>=1.0.0
httpx>=0.27.0
```

#### [NEW] `services/ingestion/loader.py`
- Extract all text from a PDF using PyMuPDF (`fitz`)
- Accept both file path (str) and file-like object (UploadFile)
- Return: `str` (full extracted text)
- Handle errors gracefully (corrupt PDFs, empty pages)

#### [NEW] `services/ingestion/chunker.py`
- Use `RecursiveCharacterTextSplitter` from LangChain
- Config: `chunk_size=500`, `chunk_overlap=50`
- Return: `list[str]` (text chunks)

#### [NEW] `services/ingestion/embedder.py`
- Load `all-MiniLM-L6-v2` model (lazy singleton)
- Accept `list[str]` → return `np.ndarray` of embeddings
- Batch encoding for efficiency

#### [NEW] `services/ingestion/indexer.py`
- Build FAISS `IndexFlatL2` from embeddings
- Persist index to disk (`data/index/`)
- Store chunk-to-text mapping alongside index
- Provide `add_to_index()` and `load_index()` functions

---

### Phase 2 — RAG Tool

#### [NEW] `tools/rag_tool.py`
- `retrieve_context(query: str, k: int = 5) → list[str]`
- Embed query → search FAISS index → return top-k chunks
- No LLM calls — pure retrieval
- Loads FAISS index from disk on first call (cached)

---

### Phase 3 — Quiz Agent

#### [NEW] `agents/base_agent.py`
- `BaseAgent` class with `rag_tool` and `llm` injected
- Shared `get_context(query)` method
- Shared `run(query)` abstract interface

#### [NEW] `agents/task/quiz_agent.py`
- Extends `BaseAgent`
- Loads `prompts/quiz_prompt.txt`
- `run(query)` → retrieves context → builds prompt → calls LLM → parses MCQs
- Returns structured `QuizResponse` (list of questions with options + correct answer)

#### [NEW] `prompts/quiz_prompt.txt`
- Template with `{context}` and `{query}` placeholders
- Instructs LLM to generate 5 MCQs in strict JSON format

---

### Phase 4 — API Layer

#### [NEW] `main.py`
- Create FastAPI app with CORS middleware
- Include router from `api/routes.py`
- Startup event: load FAISS index if available

#### [NEW] `api/routes.py`
- `POST /upload` — Accept PDF file → run ingestion pipeline → return success
- `POST /query` — Accept `QueryRequest` → dispatch to orchestrator → return response
- `GET /health` — Health check endpoint

#### [NEW] `core/schema.py`
- `QueryRequest(query: str)`
- `QuizQuestion(question, options, correct_answer, explanation)`
- `QuizResponse(questions: list[QuizQuestion])`
- `FlashCard(front, back)`
- `FlashCardResponse(cards: list[FlashCard])`
- `ReviewResponse(summary, key_points, study_plan)`
- `UploadResponse(message, filename, num_chunks)`

#### [NEW] `core/config.py`
- `Settings` class using `pydantic-settings`
- Load from `.env`: `GROQ_API_KEY`, `OPENROUTER_API_KEY`, model names
- Singleton pattern

---

### Phase 5 — Orchestrator

#### [NEW] `agents/orchestrator.py`
- `classify_intent(query) → str` — Use LLM to classify into `quiz | flashcard | review`
- `run(query)` — Classify → dispatch to correct task agent → return result
- Fallback to `review` if classification is ambiguous

---

### Phase 6 — Additional Agents

#### [NEW] `agents/task/flash_agent.py`
- Extends `BaseAgent`
- Loads `prompts/flash_prompt.txt`
- Returns `FlashCardResponse` (front/back pairs)

#### [NEW] `agents/task/review_agent.py`
- Extends `BaseAgent`
- Loads `prompts/review_prompt.txt`
- Returns `ReviewResponse` (summary + key points + study plan)

#### [NEW] `prompts/flash_prompt.txt` / `review_prompt.txt`
- Structured prompt templates with JSON output instructions

---

### Phase 7 — MCP Saving

#### [NEW] `tools/mcp_tool.py`
- `save_result(task_type, query, result) → str` — Save to `data/results/{timestamp}_{type}.json`
- `load_results(task_type) → list[dict]` — Load past results
- `get_history() → list[dict]` — Return recent session history

---

### Phase 8 — LLM Routing

#### [NEW] `tools/llm_router.py`
- `call_llm(prompt, task_type) → str`
- Route by task: `quiz` → Groq (fast), `flashcard/review` → Groq with fallback to OpenRouter
- Exponential backoff retry on 429 errors
- Configurable model names via `config.py`

---

### Phase 8.5 — State & Evaluator (Optional Enhancements)

#### [NEW] `core/state.py`
- In-memory `SessionState` with chat history and user progress tracking
- Thread-safe dictionary keyed by session ID

#### [NEW] `agents/evaluator_agent.py`
- Optional post-processing: validate JSON output from agents
- Score quiz difficulty, check flashcard quality

---

## User Review Required

> [!IMPORTANT]
> **LLM Provider API Keys**: You will need at minimum a **Groq API key** (free at [console.groq.com](https://console.groq.com)). OpenRouter is optional as a fallback. Please confirm you have or can obtain these keys.

> [!IMPORTANT]
> **Embedding Model Size**: The `all-MiniLM-L6-v2` model is ~80MB and will be downloaded on first run. The heavier `all-mpnet-base-v2` gives better accuracy but is ~420MB. Which do you prefer?

---

## Open Questions

1. **Do you want CORS configured for a specific frontend origin**, or open to all origins (`*`) for development?
2. **Should the FAISS index support multiple PDFs** (append to existing index) or reset on each upload?
3. **Do you have a preference for the LLM model on Groq?** I've defaulted to `llama-3.3-70b-versatile` but `llama-3.1-8b-instant` is faster with higher rate limits.
4. **Is the evaluator agent a priority**, or should we skip it for the initial build and add it later?

---

## Verification Plan

### Automated Tests
1. **Phase 1**: Upload a sample PDF → verify text extraction, chunking, embedding, and FAISS indexing
2. **Phase 2**: Run a similarity search query → verify relevant chunks are returned
3. **Phase 3**: Send a quiz query → verify structured MCQ JSON output
4. **Phase 4**: Hit `/upload` and `/query` endpoints via `curl` / browser → verify HTTP responses
5. **Phase 5**: Test orchestrator routing (quiz/flashcard/review queries correctly dispatched)
6. **End-to-end**: Upload PDF → query "Generate a quiz about chapter 3" → get back valid MCQs

### Manual Verification
- Test with real academic PDFs of varying complexity
- Verify FastAPI auto-docs at `/docs`
- Validate JSON response structure matches frontend expectations
- Confirm rate limit handling with Groq free tier
