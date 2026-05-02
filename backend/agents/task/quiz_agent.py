# Quiz agent — generates MCQs from document context

import logging
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class QuizAgent(BaseAgent):
    prompt_file = "quiz_prompt.txt"
    task_type = "quiz"

    def run(self, query: str, session_id: str) -> dict:
        parsed = super().run(query, session_id=session_id)

        if isinstance(parsed, list):
            return {"type": "quiz", "questions": parsed, "query": query, "count": len(parsed)}
        elif isinstance(parsed, dict) and "questions" in parsed:
            parsed["type"] = "quiz"
            parsed["query"] = query
            return parsed
        else:
            return {"type": "quiz", "questions": [], "query": query, "raw": parsed}


quiz_agent = QuizAgent()
