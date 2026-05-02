# Document loader — extracts text from uploaded files

from pathlib import Path
import io
import logging

logger = logging.getLogger(__name__)


def _extract_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF using PyMuPDF."""
    import fitz

    text_parts = []
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        for page_num, page in enumerate(doc):
            page_text = page.get_text("text")
            if page_text.strip():
                text_parts.append(page_text)
            else:
                logger.warning(f"Page {page_num + 1} has no text (might be scanned)")
        doc.close()
    except Exception as e:
        raise ValueError(f"Failed to read PDF: {e}")

    return "\n\n".join(text_parts)


def _extract_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX using python-docx."""
    from docx import Document

    try:
        doc = Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    except Exception as e:
        raise ValueError(f"Failed to read DOCX: {e}")

    return "\n\n".join(paragraphs)


def _extract_text(file_bytes: bytes) -> str:
    """Extract text from plain text files."""
    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return file_bytes.decode("latin-1")  # fallback, never fails


# Map file extensions to their extractors
EXTRACTORS = {
    ".pdf": _extract_pdf,
    ".docx": _extract_docx,
    ".txt": _extract_text,
    ".md": _extract_text,
    ".text": _extract_text,
    ".csv": _extract_text,
    ".log": _extract_text,
    ".py": _extract_text,
    ".json": _extract_text,
    ".xml": _extract_text,
    ".html": _extract_text,
    ".htm": _extract_text,
}

SUPPORTED_EXTENSIONS = set(EXTRACTORS.keys())


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Extract text from a file based on its extension."""
    ext = Path(filename).suffix.lower()

    if ext not in EXTRACTORS:
        raise ValueError(
            f"Unsupported file type '{ext}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    logger.info(f"Extracting text from '{filename}' (type: {ext})")
    text = EXTRACTORS[ext](file_bytes)

    if not text.strip():
        raise ValueError(f"No text content found in '{filename}'")

    logger.info(f"Extracted {len(text)} characters from '{filename}'")
    return text
