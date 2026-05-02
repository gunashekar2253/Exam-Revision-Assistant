"""
API Routes — Session-aware FastAPI endpoints.

Endpoints:
  POST /upload          → Upload a document (auto-creates or appends to session)
  POST /query           → Query the AI study assistant within a session
  POST /reset-session   → Clear all data for a session
  GET  /health          → Health check + index stats
  GET  /supported-formats → List supported file types
"""

import uuid
import shutil
import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from core.schema import (
    QueryRequest, QueryResponse, UploadResponse,
    HealthResponse, ResetRequest, ResetResponse, ErrorResponse,
)
from core.config import get_session_uploads_dir, get_session_dir
from core.state import add_to_history, record_upload
from services.ingestion.loader import extract_text, SUPPORTED_EXTENSIONS
from services.ingestion.chunker import chunk_text
from services.ingestion.embedder import embed_texts
from services.ingestion.indexer import build_index, get_index_stats, clear_session
import agents.orchestrator as orchestrator

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Upload Endpoint ─────────────────────────────────────────────


@router.post(
    "/upload",
    response_model=UploadResponse,
    summary="Upload a document for processing",
    description="Upload a file. If no session_id is provided, a new session is created. If a session_id is provided, the document is appended to that session's index.",
)
async def upload_document(
    file: UploadFile = File(...),
    session_id: str = Form(default=""),
):
    """Process an uploaded document through the ingestion pipeline."""
    try:
        # Auto-generate session_id if not provided (first upload)
        if not session_id or not session_id.strip():
            session_id = str(uuid.uuid4())
            logger.info(f"New session created: {session_id}")

        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        logger.info(f"[{session_id}] Upload received: {file.filename}")

        # Read file bytes
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Empty file uploaded")

        # Step 1: Extract text
        try:
            text = extract_text(file_bytes, file.filename)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Step 2: Check for duplicate filename in this session
        uploads_dir = get_session_uploads_dir(session_id)
        save_path = uploads_dir / file.filename
        if save_path.exists():
            raise HTTPException(
                status_code=409,
                detail=f"'{file.filename}' already uploaded in this session. Reset session to re-upload."
            )

        # Step 3: Chunk text
        chunks = chunk_text(text)
        if not chunks:
            raise HTTPException(status_code=400, detail="Could not create text chunks from document")

        # Step 4: Embed chunks
        embeddings = embed_texts(chunks)

        # Step 5: Build/append to session's FAISS index
        build_index(embeddings, chunks, session_id=session_id)

        # Step 6: Save raw file to session's uploads/
        with open(save_path, "wb") as f:
            f.write(file_bytes)

        # Record in session state
        record_upload(file.filename, len(chunks), session_id=session_id)

        logger.info(f"[{session_id}] Successfully processed '{file.filename}': {len(chunks)} chunks indexed")

        return UploadResponse(
            message=f"Successfully processed '{file.filename}'",
            filename=file.filename,
            num_chunks=len(chunks),
            num_characters=len(text),
            session_id=session_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{session_id}] Upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


# ── Query Endpoint ──────────────────────────────────────────────


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Query the AI study assistant",
    description="Send a study query. The orchestrator classifies intent (quiz/flashcard/review), retrieves context from the session's index, and generates a response.",
)
async def query_handler(request: QueryRequest):
    """Handle a study query through the orchestrator."""
    try:
        logger.info(f"[{request.session_id}] Query received: '{request.query[:80]}...'")

        # Run orchestrator — it classifies intent automatically
        result = orchestrator.run(
            query=request.query,
            session_id=request.session_id,
        )

        # Record in session history
        add_to_history(request.query, result.get("type", "unknown"), session_id=request.session_id)

        return QueryResponse(
            success=True,
            type=result.get("type", "unknown"),
            intent=result.get("intent", "unknown"),
            query=request.query,
            session_id=request.session_id,
            data=result,
        )

    except RuntimeError as e:
        logger.error(f"[{request.session_id}] Query failed: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"[{request.session_id}] Query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


# ── Reset Session Endpoint ──────────────────────────────────────


@router.post(
    "/reset-session",
    response_model=ResetResponse,
    summary="Reset a session",
    description="Clear all data (index, uploads, history) for a specific session.",
)
async def reset_session(request: ResetRequest):
    """Clear all data for a session."""
    try:
        session_id = request.session_id
        logger.info(f"[{session_id}] Resetting session...")

        # Clear FAISS index (memory + disk)
        clear_session(session_id)

        # Clear uploaded files
        session_dir = get_session_dir(session_id)
        uploads_dir = session_dir / "uploads"
        if uploads_dir.exists():
            shutil.rmtree(uploads_dir)
            uploads_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"[{session_id}] Session reset complete")

        return ResetResponse(
            message=f"Session '{session_id}' has been reset",
            session_id=session_id,
        )

    except Exception as e:
        logger.error(f"Reset failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


# ── Health Endpoint ─────────────────────────────────────────────


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check if the API is running and get index statistics.",
)
async def health_check(session_id: str = "default"):
    """Return health status and index stats for a session."""
    stats = get_index_stats(session_id=session_id)
    return HealthResponse(
        status="healthy",
        index_stats=stats,
    )


# ── Info Endpoint ───────────────────────────────────────────────


@router.get(
    "/supported-formats",
    summary="List supported file formats",
)
async def supported_formats():
    """Return list of supported upload file formats."""
    return {
        "supported_extensions": sorted(SUPPORTED_EXTENSIONS),
        "description": "Upload any of these file types for processing",
    }
