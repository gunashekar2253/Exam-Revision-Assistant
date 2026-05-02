# LLM router — calls Groq (primary) with OpenRouter fallback

import time
import logging
from core.config import get_settings

logger = logging.getLogger(__name__)

_groq_client = None
_openrouter_client = None


def _get_groq_client():
    global _groq_client
    if _groq_client is None:
        from groq import Groq
        settings = get_settings()
        _groq_client = Groq(api_key=settings.groq_api_key)
    return _groq_client


def _get_openrouter_client():
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


def _call_groq(prompt: str, model: str | None = None, system_prompt: str | None = None) -> str:
    """Call Groq with retry on rate limits."""
    settings = get_settings()
    client = _get_groq_client()
    model = model or settings.groq_model

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=4096,
            )
            return response.choices[0].message.content
        except Exception as e:
            if "429" in str(e) or "rate_limit" in str(e).lower():
                wait = 2 ** attempt
                logger.warning(f"Groq rate limited. Retry in {wait}s ({attempt + 1}/3)")
                time.sleep(wait)
            else:
                raise

    raise RuntimeError("Groq: max retries exceeded")


def _call_openrouter(prompt: str, system_prompt: str | None = None) -> str:
    """Call OpenRouter as fallback."""
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


def call_llm(prompt: str, task_type: str = "general", system_prompt: str | None = None, use_fast_model: bool = False) -> str:
    """Route LLM call to Groq, fallback to OpenRouter if it fails."""
    settings = get_settings()

    model = settings.groq_fast_model if (use_fast_model or task_type == "classify") else settings.groq_model
    logger.info(f"LLM call: task={task_type}, model={model}")

    try:
        return _call_groq(prompt, model=model, system_prompt=system_prompt)
    except Exception as e:
        logger.warning(f"Groq failed: {e}. Trying OpenRouter...")
        try:
            return _call_openrouter(prompt, system_prompt=system_prompt)
        except Exception as fallback_err:
            raise RuntimeError(f"All LLM providers failed. Groq: {e} | OpenRouter: {fallback_err}")
