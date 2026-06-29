"""
Provider-agnostic LLM gateway — the single call point for every completion in the system.
Model strings come only from config so swapping providers is a .env change, never a code
change. Routes through LiteLLM (uniform interface across providers). No cross-provider
fallback — Daniel and Roei each have their own keys giving double the free-tier quota.
Rate limit errors surface as a clean APIError so the frontend shows a friendly message.
"""
from __future__ import annotations

from core.config import settings
from core.errors import APIError
from core.logging import get_logger

logger = get_logger(__name__)


async def complete(
    messages: list[dict],
    model: str | None = None,
    max_tokens: int = 1000,
    **kwargs,
) -> str:
    """
    Run one LLM completion for extraction tasks (uses EXTRACTION_MODEL = Gemini 2.5 Flash).
    Raises APIError on rate limit or provider error — never falls back to a different provider.
    """
    import litellm  # lazy import — keeps startup fast

    target = model or settings.EXTRACTION_MODEL
    try:
        resp = await litellm.acompletion(
            model=target,
            messages=messages,
            max_tokens=max_tokens,
            **kwargs,
        )
        return resp.choices[0].message.content
    except litellm.exceptions.RateLimitError as exc:
        logger.warning("Rate limit on %s: %s", target, exc)
        raise APIError("rate_limit_exceeded", status_code=429)
    except Exception as exc:
        logger.error("LLM completion failed on %s: %s", target, exc)
        raise APIError("extraction_failed", status_code=502)


async def explain(
    messages: list[dict],
    max_tokens: int = 500,
    **kwargs,
) -> str:
    """
    Run one LLM completion for explanation tasks (uses EXPLANATION_MODEL = Groq gpt-oss-120b).
    Falls back to EXPLANATION_FALLBACK (gpt-oss-20b) on rate limit — same Groq key,
    smaller model with a separate quota bucket. Raises APIError if both are exhausted.
    """
    import litellm

    primary = settings.EXPLANATION_MODEL
    fallback = settings.EXPLANATION_FALLBACK

    try:
        resp = await litellm.acompletion(
            model=primary,
            messages=messages,
            max_tokens=max_tokens,
            **kwargs,
        )
        return resp.choices[0].message.content
    except litellm.exceptions.RateLimitError as exc:
        logger.warning("Rate limit on %s -> trying fallback %s (%s)", primary, fallback, exc)
        try:
            resp = await litellm.acompletion(
                model=fallback,
                messages=messages,
                max_tokens=max_tokens,
                **kwargs,
            )
            return resp.choices[0].message.content
        except litellm.exceptions.RateLimitError:
            logger.warning("Rate limit on fallback %s too — both Groq quota buckets exhausted", fallback)
            raise APIError("rate_limit_exceeded", status_code=429)
    except Exception as exc:
        logger.error("Explanation failed on %s: %s", primary, exc)
        raise APIError("extraction_failed", status_code=502)


def gateway_status() -> str:
    """'live' — always, since keys are required config fields."""
    return "live"