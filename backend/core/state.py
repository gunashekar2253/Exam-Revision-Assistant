# Session state — tracks history and uploads per session (in-memory)

import logging
from datetime import datetime
from threading import Lock

logger = logging.getLogger(__name__)

_lock = Lock()
_sessions: dict[str, dict] = {}


def get_session(session_id: str = "default") -> dict:
    """Get or create a session."""
    with _lock:
        if session_id not in _sessions:
            _sessions[session_id] = {
                "history": [],
                "created_at": datetime.now().isoformat(),
                "documents_uploaded": [],
            }
        return _sessions[session_id]


def add_to_history(query: str, response_type: str, session_id: str = "default") -> None:
    """Record a query in session history."""
    session = get_session(session_id)
    with _lock:
        session["history"].append({
            "query": query,
            "type": response_type,
            "timestamp": datetime.now().isoformat(),
        })


def record_upload(filename: str, num_chunks: int, session_id: str = "default") -> None:
    """Record a file upload in the session."""
    session = get_session(session_id)
    with _lock:
        session["documents_uploaded"].append({
            "filename": filename,
            "num_chunks": num_chunks,
            "timestamp": datetime.now().isoformat(),
        })
