# FAISS indexer — per-session vector index (build, search, persist, clear)

import json
import shutil
import logging
import threading
import numpy as np
import faiss
from pathlib import Path
from core.config import get_session_index_dir

logger = logging.getLogger(__name__)

_cache: dict[str, dict] = {}  # {session_id: {"index": faiss.Index, "chunks": [str]}}
_lock = threading.Lock()


def _get_paths(session_id: str) -> tuple[Path, Path]:
    index_dir = get_session_index_dir(session_id)
    return index_dir / "faiss.index", index_dir / "chunks.json"


def _save_chunks(chunks: list[str], session_id: str) -> None:
    _, chunks_file = _get_paths(session_id)
    with open(chunks_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False)


def _load_chunks(session_id: str) -> list[str]:
    _, chunks_file = _get_paths(session_id)
    if chunks_file.exists():
        with open(chunks_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def build_index(embeddings: np.ndarray, chunks: list[str], session_id: str) -> None:
    """Build or append to a session's FAISS index."""
    with _lock:
        index_file, _ = _get_paths(session_id)
        dimension = embeddings.shape[1]
        cached = _cache.get(session_id)

        if cached and cached["index"].d == dimension:
            # Append to existing
            logger.info(f"[{session_id}] Appending {len(chunks)} chunks")
            cached["index"].add(np.array(embeddings, dtype=np.float32))
            cached["chunks"].extend(chunks)
        else:
            # Create new index
            logger.info(f"[{session_id}] Creating new index: dim={dimension}, vectors={len(chunks)}")
            index = faiss.IndexFlatIP(dimension)
            index.add(np.array(embeddings, dtype=np.float32))
            _cache[session_id] = {"index": index, "chunks": list(chunks)}

        # Save to disk
        cached = _cache[session_id]
        faiss.write_index(cached["index"], str(index_file))
        _save_chunks(cached["chunks"], session_id)
        logger.info(f"[{session_id}] Index saved: {cached['index'].ntotal} vectors")


def load_index(session_id: str) -> bool:
    """Load a session's index from disk into memory."""
    with _lock:
        index_file, _ = _get_paths(session_id)
        if not index_file.exists():
            return False

        index = faiss.read_index(str(index_file))
        chunks = _load_chunks(session_id)
        _cache[session_id] = {"index": index, "chunks": chunks}
        logger.info(f"[{session_id}] Loaded index: {index.ntotal} vectors")
        return True


def search(query_embedding: np.ndarray, k: int = 5, session_id: str = "default") -> list[str]:
    """Search a session's index for the top-k similar chunks."""
    with _lock:
        cached = _cache.get(session_id)

        if cached is None:
            index_file, _ = _get_paths(session_id)
            if not index_file.exists():
                raise RuntimeError("No documents uploaded yet. Please upload a document first.")
            index = faiss.read_index(str(index_file))
            chunks = _load_chunks(session_id)
            _cache[session_id] = {"index": index, "chunks": chunks}
            cached = _cache[session_id]

        index = cached["index"]
        chunks = cached["chunks"]

        k = min(k, index.ntotal)
        if k == 0:
            return []

        distances, indices = index.search(np.array(query_embedding, dtype=np.float32), k)

        results = [chunks[i] for i in indices[0] if 0 <= i < len(chunks)]
        logger.info(f"[{session_id}] Found {len(results)} chunks")
        return results


def clear_session(session_id: str) -> None:
    """Remove a session's index from memory and disk."""
    with _lock:
        _cache.pop(session_id, None)
        index_dir = get_session_index_dir(session_id)
        if index_dir.exists():
            shutil.rmtree(index_dir)
            index_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"[{session_id}] Session cleared")


def get_index_stats(session_id: str = "default") -> dict:
    """Get index stats for a session."""
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
