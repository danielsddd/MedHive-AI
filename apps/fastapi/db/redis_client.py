"""
Single async Redis client used for ARQ job queuing and rate-limit counters. Self-hosted
Redis only (no Upstash daily cap — hard rule). Lazily connected and cached; ping() backs
the /healthz Redis check. URL comes from config so dev/prod differ by env only.
"""
from __future__ import annotations

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)
_client = None


def get_redis():
    global _client
    if _client is None:
        from redis.asyncio import from_url

        _client = from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    return _client


async def ping() -> bool:
    try:
        return bool(await get_redis().ping())
    except Exception as exc:
        logger.warning("Redis ping failed: %s", exc)
        return False
