# Orchestrator — classifies intent and dispatches to the right agent

import logging
from tools.llm_router import call_llm
from agents.task.quiz_agent import quiz_agent
from agents.task.flash_agent import flash_agent
from agents.task.review_agent import review_agent

logger = logging.getLogger(__name__)

# Prompt for intent classification
CLASSIFY_PROMPT = """Classify the following user query into exactly ONE of these categories:
- quiz: The user wants to be tested, wants questions, MCQs, or a quiz.
- flashcard: The user wants flashcards, memory cards, or quick-review cards.
- review: The user wants a summary, study plan, key points, explanation, or general review.

Respond with ONLY the category name (quiz, flashcard, or review). Nothing else.

User query: {query}"""


def classify_intent(query: str) -> str:
    """Use a fast LLM call to classify the intent."""
    prompt = CLASSIFY_PROMPT.format(query=query)
    result = call_llm(prompt=prompt, task_type="classify", use_fast_model=True)
    intent = result.strip().lower()

    valid = {"quiz", "flashcard", "review"}
    if intent not in valid:
        for v in valid:
            if v in intent:
                intent = v
                break
        else:
            logger.warning(f"Unknown intent '{intent}', defaulting to 'review'")
            intent = "review"

    logger.info(f"Intent: '{query[:60]}...' -> {intent}")
    return intent


AGENTS = {
    "quiz": quiz_agent,
    "flashcard": flash_agent,
    "review": review_agent,
}

# Maps common keywords to valid intents
INTENT_ALIASES = {
    "quiz": "quiz", "test": "quiz", "mcq": "quiz", "question": "quiz", "questions": "quiz",
    "flashcard": "flashcard", "flashcards": "flashcard", "flash": "flashcard", "cards": "flashcard",
    "review": "review", "summary": "review", "summarize": "review", "study plan": "review",
    "study": "review", "key points": "review", "explain": "review", "notes": "review",
}


def _normalize_intent(raw: str) -> str:
    """Normalize raw intent string to a valid agent key."""
    raw = raw.strip().lower()

    if raw in AGENTS:
        return raw
    if raw in INTENT_ALIASES:
        return INTENT_ALIASES[raw]
    for keyword, mapped in INTENT_ALIASES.items():
        if keyword in raw:
            return mapped

    logger.warning(f"Can't normalize '{raw}', defaulting to 'review'")
    return "review"


def run(query: str, session_id: str) -> dict:
    """Classify intent -> dispatch to agent -> return result."""
    intent = classify_intent(query)
    intent = _normalize_intent(intent)

    logger.info(f"[{session_id}] Dispatching to {intent} agent")
    result = AGENTS[intent].run(query, session_id=session_id)

    result["intent"] = intent
    result["session_id"] = session_id
    return result
