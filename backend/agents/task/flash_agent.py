"""
Flashcard Agent — Generates study flashcards from document context.

Inherits from BaseAgent and specializes in flashcard creation.
Returns structured flashcard data with front/back pairs.
"""

import logging
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class FlashAgent(BaseAgent):
    """Generate flashcards from document context."""

    prompt_file = "flash_prompt.txt"
    task_type = "flashcard"

    def run(self, query: str, session_id: str) -> dict:
        """
        Generate flashcards based on the query and document context.

        Returns:
            {
                "type": "flashcard",
                "cards": [...],  # List of {front, back, category}
                "query": str
            }
        """
        parsed = super().run(query, session_id=session_id)

        if isinstance(parsed, list):
            return {
                "type": "flashcard",
                "cards": parsed,
                "query": query,
                "count": len(parsed),
            }
        elif isinstance(parsed, dict) and "cards" in parsed:
            parsed["type"] = "flashcard"
            parsed["query"] = query
            return parsed
        else:
            return {
                "type": "flashcard",
                "cards": parsed if isinstance(parsed, list) else [],
                "query": query,
                "raw": parsed if not isinstance(parsed, list) else None,
            }


# Singleton instance
flash_agent = FlashAgent()
