# Request and response models

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3)
    session_id: str = Field(...)

    @field_validator("query")
    @classmethod
    def strip_and_validate_query(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Query must be at least 3 characters")
        return v


class ResetRequest(BaseModel):
    session_id: str = Field(...)


class UploadResponse(BaseModel):
    message: str
    filename: str
    num_chunks: int
    num_characters: int
    session_id: str


class QueryResponse(BaseModel):
    success: bool = True
    type: str
    intent: str
    query: str
    session_id: str
    data: dict


class HealthResponse(BaseModel):
    status: str = "healthy"
    index_stats: dict = {}


class ResetResponse(BaseModel):
    message: str
    session_id: str


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: str = ""
