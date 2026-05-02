"""
RAG Tool — Session-aware retrieval from FAISS vector store.

This is a pure retrieval tool — no LLM calls happen here.
Agents use this to fetch grounding context before generating content.
"""

import logging
from core.config import get_settings
from services.ingestion.embedder import embed_query
from services.ingestion.indexer import search

logger = logging.getLogger(__name__)


def retrieve_context(query: str, session_id: str, k: int | None = None) -> list[str]:
    """
    Retrieve the top-k most relevant text chunks for a given query.

    Args:
        query: The user's query or topic.
        session_id: Which session's index to search.
        k: Number of chunks to retrieve (defaults to config value).

    Returns:
        List of relevant text chunks, ordered by similarity.
    """
    settings = get_settings()
    k = k or settings.rag_top_k

    logger.info(f"[{session_id}] RAG retrieval: query='{query[:80]}...', k={k}")

    # Embed the query
    query_embedding = embed_query(query)

    # Search session's FAISS index
    chunks = search(query_embedding, k=k, session_id=session_id)

    logger.info(f"[{session_id}] Retrieved {len(chunks)} context chunks")
    return chunks


def format_context(chunks: list[str]) -> str:
    """
    Format retrieved chunks into a single context string for LLM prompts.

    Args:
        chunks: List of text chunks from retrieval.

    Returns:
        Formatted context string with chunk separators.
    """
    if not chunks:
        return "No relevant context found in the uploaded documents."

    formatted = []
    for i, chunk in enumerate(chunks, 1):
        formatted.append(f"[Context {i}]\n{chunk}")

    return "\n\n---\n\n".join(formatted)
