"""
Base Agent — Shared logic for all task agents.

Provides:
  - Session-aware RAG context retrieval
  - Prompt template loading
  - LLM interaction
  - JSON response parsing
"""

import json
import re
import logging
from pathlib import Path
from tools.rag_tool import retrieve_context, format_context
from tools.llm_router import call_llm
from core.config import PROMPTS_DIR

logger = logging.getLogger(__name__)


class BaseAgent:
    """
    Abstract base for all task agents (Quiz, Flashcard, Review).

    Subclasses must set:
        - prompt_file: str (filename in prompts/ directory)
        - task_type: str (for LLM routing)
    """

    prompt_file: str = ""
    task_type: str = "general"

    def __init__(self):
        self._prompt_template: str | None = None

    def _load_prompt(self) -> str:
        """Load the prompt template from disk (cached)."""
        if self._prompt_template is None:
            path = PROMPTS_DIR / self.prompt_file
            if not path.exists():
                raise FileNotFoundError(f"Prompt template not found: {path}")
            self._prompt_template = path.read_text(encoding="utf-8")
        return self._prompt_template

    def get_context(self, query: str, session_id: str) -> str:
        """Retrieve and format context from the session's vector store."""
        chunks = retrieve_context(query, session_id=session_id)
        return format_context(chunks)

    def build_prompt(self, query: str, context: str) -> str:
        """Build the final prompt by filling the template."""
        template = self._load_prompt()
        return template.replace("{context}", context).replace("{query}", query)

    def parse_json_response(self, response: str) -> dict | list:
        """
        Parse JSON from LLM response, handling common formatting issues.

        The LLM might wrap JSON in markdown code blocks — this handles that.
        """
        # Strip markdown code blocks if present
        cleaned = response.strip()
        cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```\s*$", "", cleaned)
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.debug(f"Raw response: {response[:500]}")
            # Return raw text as fallback
            return {"raw_response": response, "parse_error": str(e)}

    def run(self, query: str, session_id: str) -> dict:
        """
        Execute the agent pipeline: RAG → Prompt → LLM → Parse.

        Args:
            query: User's query or topic.
            session_id: Session to retrieve context from.

        Returns:
            Parsed response (dict or list).
        """
        logger.info(f"[{self.task_type}] Running agent for session '{session_id}', query: '{query[:80]}...'")

        # 1. Retrieve context from this session's index
        context = self.get_context(query, session_id=session_id)

        # 2. Build prompt
        prompt = self.build_prompt(query, context)

        # 3. Call LLM
        system_prompt = f"You are a specialized {self.task_type} generation agent. Always respond with valid JSON."
        raw_response = call_llm(
            prompt=prompt,
            task_type=self.task_type,
            system_prompt=system_prompt,
        )

        # 4. Parse response
        parsed = self.parse_json_response(raw_response)

        logger.info(f"[{self.task_type}] Agent completed successfully")
        return parsed
