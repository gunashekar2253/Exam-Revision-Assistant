# Base agent — shared logic for quiz, flashcard, and review agents

import json
import re
import logging
from tools.rag_tool import retrieve_context, format_context
from tools.llm_router import call_llm
from core.config import PROMPTS_DIR

logger = logging.getLogger(__name__)


class BaseAgent:
    """Parent class for all task agents. Handles RAG + LLM + JSON parsing."""

    prompt_file: str = ""
    task_type: str = "general"

    def __init__(self):
        self._prompt_template: str | None = None

    def _load_prompt(self) -> str:
        """Load prompt template from disk (cached)."""
        if self._prompt_template is None:
            path = PROMPTS_DIR / self.prompt_file
            if not path.exists():
                raise FileNotFoundError(f"Prompt not found: {path}")
            self._prompt_template = path.read_text(encoding="utf-8")
        return self._prompt_template

    def get_context(self, query: str, session_id: str) -> str:
        """Retrieve relevant chunks from the session's index."""
        chunks = retrieve_context(query, session_id=session_id)
        return format_context(chunks)

    def build_prompt(self, query: str, context: str) -> str:
        """Fill the prompt template with context and query."""
        template = self._load_prompt()
        return template.replace("{context}", context).replace("{query}", query)

    def parse_json_response(self, response: str) -> dict | list:
        """Parse JSON from LLM response, stripping markdown code blocks if present."""
        cleaned = response.strip()
        cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```\s*$", "", cleaned)
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse failed: {e}")
            return {"raw_response": response, "parse_error": str(e)}

    def run(self, query: str, session_id: str) -> dict:
        """Run the full pipeline: RAG → prompt → LLM → parse."""
        logger.info(f"[{self.task_type}] Running for '{query[:80]}...'")

        context = self.get_context(query, session_id=session_id)
        prompt = self.build_prompt(query, context)

        system_prompt = f"You are a {self.task_type} generation agent. Always respond with valid JSON."
        raw = call_llm(prompt=prompt, task_type=self.task_type, system_prompt=system_prompt)

        parsed = self.parse_json_response(raw)
        logger.info(f"[{self.task_type}] Done")
        return parsed
