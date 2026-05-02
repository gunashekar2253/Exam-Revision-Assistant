"""
AI Study Assistant — Backend Entry Point

Starts the FastAPI server with CORS, logging, and route registration.
Session-based architecture — each session has its own index.
"""

import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router

# ── Logging setup ──────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ──────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup and shutdown logic."""
    # Startup
    logger.info("Starting AI Study Assistant Backend...")
    logger.info("Session-based architecture active - each session gets isolated data")
    yield
    # Shutdown
    logger.info("Shutting down...")


# ── FastAPI App ────────────────────────────────────────────────

app = FastAPI(
    title="AI Study Assistant",
    description="Multi-agent AI backend for generating quizzes, flashcards, and study reviews from uploaded documents. Session-based isolation ensures each user's data is separate.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Open for development — restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ─────────────────────────────────────────────────────

app.include_router(router, prefix="/api")


# ── Root ───────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "name": "AI Study Assistant",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "upload": "POST /api/upload",
            "query": "POST /api/query",
            "reset": "POST /api/reset-session",
            "health": "GET /api/health",
            "formats": "GET /api/supported-formats",
        },
    }


# ── Direct run ─────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
