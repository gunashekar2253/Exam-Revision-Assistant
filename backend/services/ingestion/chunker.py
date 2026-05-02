# Text chunker — splits text into overlapping chunks

import logging
from core.config import get_settings

logger = logging.getLogger(__name__)


def chunk_text(text: str) -> list[str]:
    """Split text into chunks for embedding."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    settings = get_settings()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_text(text)
    logger.info(f"Split text into {len(chunks)} chunks (size={settings.chunk_size}, overlap={settings.chunk_overlap})")

    return chunks
