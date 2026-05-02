"""
Review Agent — Generates summaries, key points, and study plans.

Inherits from BaseAgent and specializes in content review.
Returns structured review data with summary, key points, and study plan.
"""

import logging
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ReviewAgent(BaseAgent):
    """Generate comprehensive study reviews from document context."""

    prompt_file = "review_prompt.txt"
    task_type = "review"

    def run(self, query: str, session_id: str) -> dict:
        """
        Generate a review based on the query and document context.

        Returns:
            {
                "type": "review",
                "summary": str,
                "key_points": [...],
                "study_plan": [...],
                "exam_topics": [...],
                "query": str
            }
        """
        parsed = super().run(query, session_id=session_id)

        if isinstance(parsed, dict):
            parsed["type"] = "review"
            parsed["query"] = query
            return parsed
        else:
            return {
                "type": "review",
                "summary": str(parsed),
                "key_points": [],
                "study_plan": [],
                "exam_topics": [],
                "query": query,
            }


# Singleton instance
review_agent = ReviewAgent()
