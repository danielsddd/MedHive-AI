"""
Provider-agnostic LLM gateway — the single call point for every completion in the system.
Model strings come only from config, so swapping Gemini -> Groq -> Cerebras -> GitHub Models
is a .env change, never a code change. Routes through LiteLLM (uniform interface across
providers) with an automatic primary->fallback on rate limits. When no provider key is
present (offline mode) it returns a deterministic stub completion so flows and tests run
end-to-end with zero setup.
"""
from __future__ import annotations

import json

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


def _stub_completion(messages: list[dict]) -> str:
    """Offline placeholder so the pipeline never hard-fails without keys (dev only)."""
    last = messages[-1]["content"] if messages else ""
    return json.dumps({"stub": True, "echo": str(last)[:200]})


async def complete(
    messages: list[dict],
    model: str | None = None,
    fallback: str | None = None,
    max_tokens: int = 1000,
    **kwargs,
) -> str:
    """Run one completion. Falls back to the secondary model on rate-limit errors."""
    if not settings.llm_is_live():
        logger.info("LLM gateway in OFFLINE mode — returning stub completion.")
        return _stub_completion(messages)

    import litellm  # imported lazily so offline mode needs no LLM stack

    primary = model or settings.EXTRACTION_MODEL
    secondary = fallback or settings.EXTRACTION_FALLBACK
    try:
        resp = await litellm.acompletion(
            model=primary, messages=messages, max_tokens=max_tokens, **kwargs
        )
        return resp.choices[0].message.content
    except litellm.exceptions.RateLimitError as exc:
        logger.warning("Rate limit on %s -> falling back to %s (%s)", primary, secondary, exc)
        resp = await litellm.acompletion(
            model=secondary, messages=messages, max_tokens=max_tokens, **kwargs
        )
        return resp.choices[0].message.content


def gateway_status() -> str:
    """'live' | 'offline' — surfaced by /healthz without exposing keys."""
    return "live" if settings.llm_is_live() else "offline"
