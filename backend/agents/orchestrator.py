"""
Orchestrator — Intent classification and agent dispatch.

Determines which task agent to call based on the user's query,
then routes the request to the appropriate agent.
All operations are session-aware.
"""

import logging
from tools.llm_router import call_llm
from agents.task.quiz_agent import quiz_agent
from agents.task.flash_agent import flash_agent
from agents.task.review_agent import review_agent

logger = logging.getLogger(__name__)

# ── Intent classification ──────────────────────────────────────

CLASSIFY_PROMPT = """Classify the following user query into exactly ONE of these categories:
- quiz: The user wants to be tested, wants questions, MCQs, or a quiz.
- flashcard: The user wants flashcards, memory cards, or quick-review cards.
- review: The user wants a summary, study plan, key points, explanation, or general review.

Respond with ONLY the category name (quiz, flashcard, or review). Nothing else.

User query: {query}"""


def classify_intent(query: str) -> str:
    """
    Use a fast LLM call to classify the user's intent.

    Returns:
        One of: "quiz", "flashcard", "review"
    """
    prompt = CLASSIFY_PROMPT.format(query=query)

    result = call_llm(
        prompt=prompt,
        task_type="classify",
        use_fast_model=True,  # Use fast model for classification
    )

    intent = result.strip().lower()

    # Validate — default to review if unclear
    valid_intents = {"quiz", "flashcard", "review"}
    if intent not in valid_intents:
        # Try to find a valid intent in the response
        for valid in valid_intents:
            if valid in intent:
                intent = valid
                break
        else:
            logger.warning(f"Could not classify intent '{intent}', defaulting to 'review'")
            intent = "review"

    logger.info(f"Classified intent: '{query[:60]}...' -> {intent}")
    return intent


# ── Agent dispatch ─────────────────────────────────────────────

AGENTS = {
    "quiz": quiz_agent,
    "flashcard": flash_agent,
    "review": review_agent,
}

# Alias map — routes common keywords to valid intents
INTENT_ALIASES = {
    "quiz": "quiz", "test": "quiz", "mcq": "quiz", "question": "quiz", "questions": "quiz",
    "flashcard": "flashcard", "flashcards": "flashcard", "flash": "flashcard", "cards": "flashcard", "memory": "flashcard",
    "review": "review", "summary": "review", "summarize": "review", "study plan": "review",
    "study": "review", "key points": "review", "explain": "review", "notes": "review",
}


def _normalize_intent(raw_intent: str) -> str:
    """Normalize a raw intent string to a valid agent key."""
    raw = raw_intent.strip().lower()

    # Direct match
    if raw in AGENTS:
        return raw

    # Alias match
    if raw in INTENT_ALIASES:
        return INTENT_ALIASES[raw]

    # Substring match — find any alias keyword inside the raw string
    for keyword, mapped in INTENT_ALIASES.items():
        if keyword in raw:
            return mapped

    # Default fallback
    logger.warning(f"Could not normalize intent '{raw_intent}', defaulting to 'review'")
    return "review"


def run(query: str, session_id: str) -> dict:
    """
    Orchestrate a query: classify intent -> dispatch to agent -> return result.

    Args:
        query: The user's query.
        session_id: Session to operate on.

    Returns:
        Agent response dict.
    """
    # Step 1: Classify intent via LLM
    intent = classify_intent(query)

    # Step 2: Normalize to a valid agent key
    intent = _normalize_intent(intent)

    # Step 3: Dispatch to agent with session context
    agent = AGENTS[intent]

    logger.info(f"[{session_id}] Dispatching to {intent} agent")
    result = agent.run(query, session_id=session_id)

    # Step 4: Add metadata
    result["intent"] = intent
    result["session_id"] = session_id

    return result
