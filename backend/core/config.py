# Core config — loads .env settings and defines paths

from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SESSIONS_DIR = DATA_DIR / "sessions"
PROMPTS_DIR = BASE_DIR / "prompts"

DATA_DIR.mkdir(parents=True, exist_ok=True)
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def get_session_dir(session_id: str) -> Path:
    """Get the data directory for a session."""
    session_dir = SESSIONS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def get_session_index_dir(session_id: str) -> Path:
    """Get the FAISS index directory for a session."""
    index_dir = get_session_dir(session_id) / "index"
    index_dir.mkdir(parents=True, exist_ok=True)
    return index_dir


def get_session_uploads_dir(session_id: str) -> Path:
    """Get the uploads directory for a session."""
    uploads_dir = get_session_dir(session_id) / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    return uploads_dir


class Settings(BaseSettings):
    """All settings loaded from .env file."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API keys
    groq_api_key: str = ""
    gemini_api_key: str = ""
    openrouter_api_key: str = ""

    # Model names
    groq_model: str = "llama-3.3-70b-versatile"
    groq_fast_model: str = "llama-3.1-8b-instant"
    openrouter_model: str = "meta-llama/llama-3.3-70b-instruct"

    # Embedding
    embedding_model: str = "gemini-embedding-001"

    # Chunking
    chunk_size: int = 500
    chunk_overlap: int = 50

    # RAG
    rag_top_k: int = 5


@lru_cache()
def get_settings() -> Settings:
    return Settings()
