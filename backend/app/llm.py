import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def call_openrouter(
    prompt: str,
    *,
    system_prompt: str | None = None,
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int | None = None,
    timeout: float = 45.0,
    response_format: dict | None = None,
) -> str:
    """Single OpenRouter chat-completion entry point. Returns the raw content string.

    Soft-fails (returns "") when OPENROUTER_API_KEY is not configured so callers
    don't need to gate every call site.
    """
    if not settings.OPENROUTER_API_KEY:
        return ""

    messages: list[dict] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload: dict = {
        "model": model or settings.OPENROUTER_MODEL,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if response_format is not None:
        payload["response_format"] = response_format

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=timeout) as client:
        response = client.post(
            settings.OPENROUTER_BASE_URL,
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
