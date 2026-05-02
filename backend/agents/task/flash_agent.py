# Flashcard agent — generates front/back study cards

import logging
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class FlashAgent(BaseAgent):
    prompt_file = "flash_prompt.txt"
    task_type = "flashcard"

    def run(self, query: str, session_id: str) -> dict:
        parsed = super().run(query, session_id=session_id)

        if isinstance(parsed, list):
            return {"type": "flashcard", "cards": parsed, "query": query, "count": len(parsed)}
        elif isinstance(parsed, dict) and "cards" in parsed:
            parsed["type"] = "flashcard"
            parsed["query"] = query
            return parsed
        else:
            return {"type": "flashcard", "cards": [], "query": query, "raw": parsed}


flash_agent = FlashAgent()
