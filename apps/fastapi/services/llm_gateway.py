"""
Provider-agnostic LLM gateway — the single call point for every completion in the system.
Model strings come only from config so swapping providers is a .env change, never a code
change. Routes through LiteLLM (uniform interface). On a rate-limit error, automatically
rotates to the next available key for that provider (Daniel -> Roei) before giving up —
this is key rotation, not a different provider/model, so accuracy is unaffected. Only after
every key for a provider is exhausted does a clean APIError surface to the caller.
"""
from __future__ import annotations

from core.errors import ERRORS, APIError
from core.logging import get_logger

from core.config import settings

logger = get_logger(__name__)


async def _try_keys(
    model: str, keys: list[str], messages: list[dict], max_tokens: int, **kwargs
) -> str:
    """Try each key in order; rotate to the next on RateLimitError. Raise on full exhaustion."""
    import litellm

    last_exc: Exception | None = None
    for i, key in enumerate(keys):
        try:
            resp = await litellm.acompletion(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                api_key=key,
                **kwargs,
            )
            return resp.choices[0].message.content
        except litellm.exceptions.RateLimitError as exc:
            last_exc = exc
            who = "Daniel" if i == 0 else "Roei"
            logger.warning(
                "Rate limit on %s (key #%d/%s) -> rotating to next key", model, i + 1, who
            )
            continue
        except Exception as exc:
            logger.error("LLM call failed on %s: %s", model, exc)
            raise APIError(
                "extraction_failed", ERRORS["extraction_failed"], status_code=502
            ) from exc

    logger.warning("All keys exhausted for %s: %s", model, last_exc)
    raise APIError(
        "rate_limit_exceeded", ERRORS["rate_limit_exceeded"], status_code=429
    ) from last_exc


async def complete(
    messages: list[dict],
    model: str | None = None,
    max_tokens: int = 1000,
    **kwargs,
) -> str:
    """Extraction calls — Gemini. Rotates across all configured Gemini keys on rate limit."""
    target = model or settings.EXTRACTION_MODEL
    keys = settings.gemini_keys()
    if not keys:
        raise APIError(
            "provider_unavailable", "No API key configured for this provider.", status_code=503
        )
    return await _try_keys(target, keys, messages, max_tokens, **kwargs)


async def explain(
    messages: list[dict],
    max_tokens: int = 500,
    **kwargs,
) -> str:
    """
    Explanation calls — Groq. Rotates across Groq keys (Daniel -> Roei) on the primary
    model; if every key is exhausted on the primary, retries the same key rotation on the
    fallback model (same provider, smaller model, separate quota bucket).
    """
    keys = settings.groq_keys()
    if not keys:
        raise APIError(
            "provider_unavailable", "No API key configured for this provider.", status_code=503
        )

    try:
        return await _try_keys(settings.EXPLANATION_MODEL, keys, messages, max_tokens, **kwargs)
    except APIError as primary_exhausted:
        if primary_exhausted.status_code != 429:
            raise
        logger.warning(
            "All keys exhausted on %s -> trying fallback %s",
            settings.EXPLANATION_MODEL,
            settings.EXPLANATION_FALLBACK,
        )
        return await _try_keys(
            settings.EXPLANATION_FALLBACK, keys, messages, max_tokens, **kwargs
        )


def gateway_status() -> str:
    """'live' iff at least one Gemini key and one Groq key are configured."""
    return "live" if settings.llm_is_live() else "down"