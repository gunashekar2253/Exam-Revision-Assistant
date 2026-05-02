"""
Pydantic Schemas — Request and response models for the API.

These enforce validation, serialization, and auto-documentation.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


# ── Request Models ──────────────────────────────────────────────


class QueryRequest(BaseModel):
    """Request body for /query endpoint."""
    query: str = Field(..., min_length=3, description="The user's study query or topic")
    session_id: str = Field(..., description="Session ID (returned from /upload)")

    @field_validator("query")
    @classmethod
    def strip_and_validate_query(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Query must be at least 3 characters after trimming whitespace")
        return v


class ResetRequest(BaseModel):
    """Request body for /reset-session endpoint."""
    session_id: str = Field(..., description="Session ID to reset")


# ── Response Models ─────────────────────────────────────────────


class UploadResponse(BaseModel):
    """Response for /upload endpoint."""
    message: str
    filename: str
    num_chunks: int
    num_characters: int
    session_id: str


class QuizQuestion(BaseModel):
    """A single MCQ question."""
    question: str
    options: dict
    correct_answer: str
    explanation: str = ""
    difficulty: str = "medium"


class FlashCard(BaseModel):
    """A single flashcard."""
    front: str
    back: str
    category: str = "concept"


class StudyStep(BaseModel):
    """A single step in a study plan."""
    step: int
    action: str
    duration: str = ""
    focus: str = ""


class QueryResponse(BaseModel):
    """Generic response wrapper for /query endpoint."""
    success: bool = True
    type: str  # quiz, flashcard, review
    intent: str
    query: str
    session_id: str
    data: dict  # The actual agent response


class HealthResponse(BaseModel):
    """Response for /health endpoint."""
    status: str = "healthy"
    index_stats: dict = {}


class ResetResponse(BaseModel):
    """Response for /reset-session endpoint."""
    message: str
    session_id: str


class ErrorResponse(BaseModel):
    """Error response."""
    success: bool = False
    error: str
    detail: str = ""
