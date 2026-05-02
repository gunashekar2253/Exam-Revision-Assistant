"""
Core configuration — loads settings from .env using pydantic-settings.
All configurable values (API keys, model names, chunk params) live here.
"""

from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


# ── Project paths ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SESSIONS_DIR = DATA_DIR / "sessions"
PROMPTS_DIR = BASE_DIR / "prompts"

# Ensure base directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def get_session_dir(session_id: str) -> Path:
    """Get (and create) the data directory for a specific session."""
    session_dir = SESSIONS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def get_session_index_dir(session_id: str) -> Path:
    """Get (and create) the FAISS index directory for a session."""
    index_dir = get_session_dir(session_id) / "index"
    index_dir.mkdir(parents=True, exist_ok=True)
    return index_dir


def get_session_uploads_dir(session_id: str) -> Path:
    """Get (and create) the uploads directory for a session."""
    uploads_dir = get_session_dir(session_id) / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    return uploads_dir


class Settings(BaseSettings):
    """Application settings — populated from .env file."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── LLM Provider Keys ──────────────────────────────────────
    groq_api_key: str = ""
    gemini_api_key: str = ""
    openrouter_api_key: str = ""

    # ── Model Configuration ────────────────────────────────────
    groq_model: str = "llama-3.3-70b-versatile"
    groq_fast_model: str = "llama-3.1-8b-instant"
    openrouter_model: str = "meta-llama/llama-3.3-70b-instruct"

    # ── Embedding Configuration (Gemini) ───────────────────────
    embedding_model: str = "gemini-embedding-001"

    # ── Chunking Configuration ─────────────────────────────────
    chunk_size: int = 500
    chunk_overlap: int = 50

    # ── RAG Configuration ──────────────────────────────────────
    rag_top_k: int = 5


@lru_cache()
def get_settings() -> Settings:
    """Cached singleton — call this everywhere instead of constructing Settings()."""
    return Settings()
