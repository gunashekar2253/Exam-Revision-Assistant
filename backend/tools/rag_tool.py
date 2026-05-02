# RAG tool — retrieves relevant context from FAISS

import logging
from core.config import get_settings
from services.ingestion.embedder import embed_query
from services.ingestion.indexer import search

logger = logging.getLogger(__name__)


def retrieve_context(query: str, session_id: str, k: int | None = None) -> list[str]:
    """Get top-k relevant chunks for a query from the session's index."""
    settings = get_settings()
    k = k or settings.rag_top_k

    logger.info(f"[{session_id}] RAG: query='{query[:80]}...', k={k}")

    query_embedding = embed_query(query)
    chunks = search(query_embedding, k=k, session_id=session_id)

    logger.info(f"[{session_id}] Retrieved {len(chunks)} chunks")
    return chunks


def format_context(chunks: list[str]) -> str:
    """Format chunks into a single string for the LLM prompt."""
    if not chunks:
        return "No relevant context found in the uploaded documents."

    formatted = [f"[Context {i}]\n{chunk}" for i, chunk in enumerate(chunks, 1)]
    return "\n\n---\n\n".join(formatted)
