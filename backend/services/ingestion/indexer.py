"""
FAISS Indexer — Session-aware vector index management.

Each session gets its own FAISS index stored at:
  data/sessions/{session_id}/index/faiss.index
  data/sessions/{session_id}/index/chunks.json

Supports: build, load, search, clear per session.
"""

import json
import shutil
import logging
import threading
import numpy as np
import faiss
from pathlib import Path
from core.config import get_session_index_dir

logger = logging.getLogger(__name__)

# ── In-memory cache (keyed by session_id) ──────────────────────

_cache: dict[str, dict] = {}
_lock = threading.Lock()


def _get_paths(session_id: str) -> tuple[Path, Path]:
    """Get the index and chunks file paths for a session."""
    index_dir = get_session_index_dir(session_id)
    return index_dir / "faiss.index", index_dir / "chunks.json"


def _save_chunks(chunks: list[str], session_id: str) -> None:
    """Persist chunk texts to disk for a session."""
    _, chunks_file = _get_paths(session_id)
    with open(chunks_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False)


def _load_chunks(session_id: str) -> list[str]:
    """Load chunk texts from disk for a session."""
    _, chunks_file = _get_paths(session_id)
    if chunks_file.exists():
        with open(chunks_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


# ── Public API ──────────────────────────────────────────────────


def build_index(embeddings: np.ndarray, chunks: list[str], session_id: str) -> None:
    """
    Build (or append to) a FAISS index for a specific session.

    Args:
        embeddings: numpy array of shape (n, dim).
        chunks: Corresponding text chunks (same order as embeddings).
        session_id: The session to store the index under.
    """
    with _lock:
        index_file, _ = _get_paths(session_id)
        dimension = embeddings.shape[1]

        # Check if session already has an index in cache
        cached = _cache.get(session_id)

        if cached and cached["index"].d == dimension:
            # Append to existing index
            logger.info(f"[{session_id}] Appending {len(chunks)} chunks to existing index")
            cached["index"].add(np.array(embeddings, dtype=np.float32))
            cached["chunks"].extend(chunks)
        else:
            # Create new index for this session
            logger.info(f"[{session_id}] Creating new FAISS index: dim={dimension}, vectors={len(chunks)}")
            index = faiss.IndexFlatIP(dimension)
            index.add(np.array(embeddings, dtype=np.float32))
            _cache[session_id] = {"index": index, "chunks": list(chunks)}

        # Persist to disk
        cached = _cache[session_id]
        faiss.write_index(cached["index"], str(index_file))
        _save_chunks(cached["chunks"], session_id)
        logger.info(f"[{session_id}] Index saved: {cached['index'].ntotal} total vectors")


def load_index(session_id: str) -> bool:
    """
    Load a session's FAISS index from disk into memory cache.

    Returns:
        True if loaded successfully, False if no index exists.
    """
    with _lock:
        index_file, _ = _get_paths(session_id)

        if not index_file.exists():
            logger.warning(f"[{session_id}] No FAISS index found on disk")
            return False

        index = faiss.read_index(str(index_file))
        chunks = _load_chunks(session_id)
        _cache[session_id] = {"index": index, "chunks": chunks}
        logger.info(f"[{session_id}] Loaded FAISS index: {index.ntotal} vectors, {len(chunks)} chunks")
        return True


def search(query_embedding: np.ndarray, k: int = 5, session_id: str = "default") -> list[str]:
    """
    Search a session's FAISS index for the top-k most similar chunks.

    Args:
        query_embedding: numpy array of shape (1, dim).
        k: Number of results to return.
        session_id: Which session's index to search.

    Returns:
        List of matching text chunks, ordered by relevance.

    Raises:
        RuntimeError: If no index is loaded for this session.
    """
    with _lock:
        cached = _cache.get(session_id)

        if cached is None:
            # Try loading from disk
            index_file, _ = _get_paths(session_id)
            if not index_file.exists():
                raise RuntimeError(
                    "No documents uploaded yet. Please upload a document first."
                )
            index = faiss.read_index(str(index_file))
            chunks = _load_chunks(session_id)
            _cache[session_id] = {"index": index, "chunks": chunks}
            cached = _cache[session_id]

        index = cached["index"]
        chunks = cached["chunks"]

        # Clamp k to available vectors
        k = min(k, index.ntotal)
        if k == 0:
            return []

        distances, indices = index.search(np.array(query_embedding, dtype=np.float32), k)

        results = []
        for i in indices[0]:
            if 0 <= i < len(chunks):
                results.append(chunks[i])

        logger.info(f"[{session_id}] Search returned {len(results)} chunks")
        return results


def clear_session(session_id: str) -> None:
    """
    Completely remove a session's index from memory and disk.

    Args:
        session_id: The session to clear.
    """
    with _lock:
        # Remove from memory cache
        _cache.pop(session_id, None)

        # Remove from disk
        index_dir = get_session_index_dir(session_id)
        if index_dir.exists():
            shutil.rmtree(index_dir)
            index_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"[{session_id}] Session index cleared")


def get_index_stats(session_id: str = "default") -> dict:
    """Return current index statistics for a session."""
    with _lock:
        cached = _cache.get(session_id)

        if cached is None:
            index_file, _ = _get_paths(session_id)
            if index_file.exists():
                index = faiss.read_index(str(index_file))
                chunks = _load_chunks(session_id)
                _cache[session_id] = {"index": index, "chunks": chunks}
                cached = _cache[session_id]

        return {
            "session_id": session_id,
            "total_vectors": cached["index"].ntotal if cached else 0,
            "total_chunks": len(cached["chunks"]) if cached else 0,
            "index_exists": cached is not None,
        }
