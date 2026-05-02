"""
Quiz Agent — Generates MCQs from uploaded document context.

Inherits from BaseAgent and specializes in quiz generation.
Returns structured quiz data with questions, options, and explanations.
"""

import logging
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class QuizAgent(BaseAgent):
    """Generate multiple-choice questions from document context."""

    prompt_file = "quiz_prompt.txt"
    task_type = "quiz"

    def run(self, query: str, session_id: str) -> dict:
        """
        Generate a quiz based on the query and document context.

        Returns:
            {
                "type": "quiz",
                "questions": [...],  # List of MCQ objects
                "query": str
            }
        """
        parsed = super().run(query, session_id=session_id)

        # Wrap in consistent response format
        if isinstance(parsed, list):
            return {
                "type": "quiz",
                "questions": parsed,
                "query": query,
                "count": len(parsed),
            }
        elif isinstance(parsed, dict) and "questions" in parsed:
            parsed["type"] = "quiz"
            parsed["query"] = query
            return parsed
        else:
            # Fallback — return whatever we got
            return {
                "type": "quiz",
                "questions": parsed if isinstance(parsed, list) else [],
                "query": query,
                "raw": parsed if not isinstance(parsed, list) else None,
            }


# Singleton instance
quiz_agent = QuizAgent()
