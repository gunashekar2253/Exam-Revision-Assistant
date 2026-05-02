"""
Embedder — Converts text chunks into vector embeddings using Gemini API.

Uses Google's Gemini embedding model via the google-genai SDK.

"""

import time
import numpy as np
import logging
from core.config import get_settings

logger = logging.getLogger(__name__)

# ── Lazy singleton client ───────────────────────────────────────

_client = None


def _get_client():
    """Initialize Gemini client once and cache it."""
    global _client
    if _client is None:
        from google import genai
        settings = get_settings()
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY not set in .env")
        _client = genai.Client(api_key=settings.gemini_api_key)
        logger.info("Gemini embedding client initialized")
    return _client


def _embed_with_retry(client, model, contents, task_type, max_retries=5):
    """Call Gemini embed API with rate-limit-aware retry."""
    for attempt in range(max_retries):
        try:
            response = client.models.embed_content(
                model=model,
                contents=contents,
                config={"task_type": task_type},
            )
            return response
        except Exception as e:
            error_str = str(e).lower()
            is_retryable = any(kw in error_str for kw in ["429", "rate", "quota", "resource_exhausted"])

            if is_retryable and attempt < max_retries - 1:
                # Gemini free tier needs ~30s to reset quota
                wait = [10, 30, 45, 60][min(attempt, 3)]
                logger.warning(
                    f"Gemini rate limited. Waiting {wait}s before retry "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(wait)
            else:
                raise


# ── Public API ──────────────────────────────────────────────────


def embed_texts(texts: list[str]) -> np.ndarray:
    """
    Convert a list of text strings into vector embeddings via Gemini API.

    Uses task_type=RETRIEVAL_DOCUMENT for optimal RAG document indexing.
    Includes retry logic for rate limit errors.

    Args:
        texts: List of text chunks to embed.

    Returns:
        numpy array of shape (len(texts), embedding_dim).
    """
    client = _get_client()
    settings = get_settings()
    logger.info(f"Embedding {len(texts)} text chunks via Gemini...")

    all_embeddings = []

    # Smaller batches + delay to stay under Gemini free tier (100 req/min)
    batch_size = 20
    total_batches = (len(texts) + batch_size - 1) // batch_size

    for batch_num, i in enumerate(range(0, len(texts), batch_size), 1):
        batch = texts[i : i + batch_size]

        logger.info(f"Embedding batch {batch_num}/{total_batches} ({len(batch)} chunks)...")
        response = _embed_with_retry(
            client, settings.embedding_model, batch, "RETRIEVAL_DOCUMENT"
        )

        for emb in response.embeddings:
            all_embeddings.append(emb.values)

        # Delay between batches to avoid hitting rate limits
        if i + batch_size < len(texts):
            time.sleep(1.5)

    embeddings = np.array(all_embeddings, dtype=np.float32)
    logger.info(f"Generated embeddings: shape={embeddings.shape}")
    return embeddings


def embed_query(query: str) -> np.ndarray:
    """
    Embed a single query string via Gemini API.

    Uses task_type=RETRIEVAL_QUERY for optimal RAG query matching.

    Args:
        query: The search query to embed.

    Returns:
        numpy array of shape (1, embedding_dim).
    """
    client = _get_client()
    settings = get_settings()

    response = _embed_with_retry(
        client, settings.embedding_model, query, "RETRIEVAL_QUERY"
    )

    embedding = np.array([response.embeddings[0].values], dtype=np.float32)
    return embedding
