# API routes — upload, query, reset, health

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


@router.post("/upload", response_model=UploadResponse, summary="Upload a document")
async def upload_document(
    file: UploadFile = File(...),
    session_id: str = Form(default=""),
):
    """Process a document through the ingestion pipeline."""
    try:
        # Auto-create session if none provided
        if not session_id or not session_id.strip():
            session_id = str(uuid.uuid4())
            logger.info(f"New session: {session_id}")

        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        logger.info(f"[{session_id}] Upload: {file.filename}")

        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Empty file")

        # Extract text
        try:
            text = extract_text(file_bytes, file.filename)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Check for duplicate filename
        uploads_dir = get_session_uploads_dir(session_id)
        save_path = uploads_dir / file.filename
        if save_path.exists():
            raise HTTPException(
                status_code=409,
                detail=f"'{file.filename}' already uploaded. Reset session to re-upload."
            )

        # Chunk -> embed -> index
        chunks = chunk_text(text)
        if not chunks:
            raise HTTPException(status_code=400, detail="Could not create chunks from document")

        embeddings = embed_texts(chunks)
        build_index(embeddings, chunks, session_id=session_id)

        # Save raw file
        with open(save_path, "wb") as f:
            f.write(file_bytes)

        record_upload(file.filename, len(chunks), session_id=session_id)
        logger.info(f"[{session_id}] Processed '{file.filename}': {len(chunks)} chunks")

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


@router.post("/query", response_model=QueryResponse, summary="Query the study assistant")
async def query_handler(request: QueryRequest):
    """Classify intent and generate response."""
    try:
        logger.info(f"[{request.session_id}] Query: '{request.query[:80]}...'")

        result = orchestrator.run(query=request.query, session_id=request.session_id)
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
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.post("/reset-session", response_model=ResetResponse, summary="Reset a session")
async def reset_session(request: ResetRequest):
    """Clear all data for a session."""
    try:
        sid = request.session_id
        logger.info(f"[{sid}] Resetting...")

        clear_session(sid)

        # Also clear uploaded files
        session_dir = get_session_dir(sid)
        uploads_dir = session_dir / "uploads"
        if uploads_dir.exists():
            shutil.rmtree(uploads_dir)
            uploads_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"[{sid}] Reset complete")
        return ResetResponse(message=f"Session '{sid}' reset", session_id=sid)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check(session_id: str = "default"):
    stats = get_index_stats(session_id=session_id)
    return HealthResponse(status="healthy", index_stats=stats)


@router.get("/supported-formats", summary="List supported file formats")
async def supported_formats():
    return {
        "supported_extensions": sorted(SUPPORTED_EXTENSIONS),
        "description": "Upload any of these file types",
    }
