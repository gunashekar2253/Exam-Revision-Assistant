# Review agent — generates summaries, key points, and study plans

import logging
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ReviewAgent(BaseAgent):
    prompt_file = "review_prompt.txt"
    task_type = "review"

    def run(self, query: str, session_id: str) -> dict:
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


review_agent = ReviewAgent()
