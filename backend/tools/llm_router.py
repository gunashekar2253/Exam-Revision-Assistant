"""
LLM Router — Abstraction layer for calling LLMs.

Routes requests to the appropriate provider (Groq primary, OpenRouter fallback).
Handles retries with exponential backoff on rate limit errors.
"""

import time
import json
import logging
from core.config import get_settings

logger = logging.getLogger(__name__)

# ── Groq Client (lazy) ─────────────────────────────────────────

_groq_client = None


def _get_groq_client():
    """Lazy-load Groq client."""
    global _groq_client
    if _groq_client is None:
        from groq import Groq
        settings = get_settings()
        _groq_client = Groq(api_key=settings.groq_api_key)
    return _groq_client


# ── OpenRouter Client (lazy) ───────────────────────────────────

_openrouter_client = None


def _get_openrouter_client():
    """Lazy-load OpenRouter client (uses OpenAI-compatible API)."""
    global _openrouter_client
    if _openrouter_client is None:
        from openai import OpenAI
        settings = get_settings()
        if not settings.openrouter_api_key:
            return None
        _openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
        )
    return _openrouter_client


# ── Core LLM call with retry ──────────────────────────────────


def _call_groq(prompt: str, model: str | None = None, system_prompt: str | None = None) -> str:
    """Call Groq API with retry logic."""
    settings = get_settings()
    client = _get_groq_client()
    model = model or settings.groq_model

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=4096,
            )
            return response.choices[0].message.content
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate_limit" in error_str.lower():
                wait_time = 2 ** attempt
                logger.warning(f"Groq rate limited. Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                raise

    raise RuntimeError("Groq API: max retries exceeded due to rate limiting")


def _call_openrouter(prompt: str, system_prompt: str | None = None) -> str:
    """Call OpenRouter API as fallback."""
    settings = get_settings()
    client = _get_openrouter_client()

    if client is None:
        raise RuntimeError("OpenRouter API key not configured")

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=settings.openrouter_model,
        messages=messages,
        temperature=0.7,
        max_tokens=4096,
    )
    return response.choices[0].message.content


# ── Public API ──────────────────────────────────────────────────


def call_llm(
    prompt: str,
    task_type: str = "general",
    system_prompt: str | None = None,
    use_fast_model: bool = False,
) -> str:
    """
    Route an LLM call to the best available provider.

    Args:
        prompt: The user/agent prompt to send.
        task_type: Type of task (quiz, flashcard, review, classify).
        system_prompt: Optional system-level instruction.
        use_fast_model: If True, use the faster/smaller model.

    Returns:
        LLM response text.
    """
    settings = get_settings()

    # Choose model based on task
    if use_fast_model or task_type == "classify":
        model = settings.groq_fast_model
    else:
        model = settings.groq_model

    logger.info(f"LLM call: task={task_type}, model={model}")

    try:
        return _call_groq(prompt, model=model, system_prompt=system_prompt)
    except Exception as e:
        logger.warning(f"Groq failed: {e}. Trying OpenRouter fallback...")
        try:
            return _call_openrouter(prompt, system_prompt=system_prompt)
        except Exception as fallback_err:
            logger.error(f"All LLM providers failed: {fallback_err}")
            raise RuntimeError(f"All LLM providers failed. Groq: {e} | OpenRouter: {fallback_err}")
