"""
Thin async Postgres access layer built on a shared asyncpg connection pool. Created once
at startup (init_pool) and reused for the process lifetime; ping() backs the /healthz DB
check. Helper functions (execute/fetch/fetchrow/fetchval) use $1-style parameters only —
never string interpolation — to keep every query injection-safe by construction.
"""
from __future__ import annotations

from typing import Any

import asyncpg

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)
_pool: asyncpg.Pool | None = None


async def init_pool() -> None:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(dsn=settings.asyncpg_dsn, min_size=1, max_size=10)
        logger.info("Postgres pool initialised.")


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def _require_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("DB pool not initialised. Call init_pool() at startup.")
    return _pool


async def execute(query: str, *args: Any) -> str:
    async with _require_pool().acquire() as conn:
        return await conn.execute(query, *args)


async def fetch(query: str, *args: Any) -> list[asyncpg.Record]:
    async with _require_pool().acquire() as conn:
        return await conn.fetch(query, *args)


async def fetchrow(query: str, *args: Any) -> asyncpg.Record | None:
    async with _require_pool().acquire() as conn:
        return await conn.fetchrow(query, *args)


async def fetchval(query: str, *args: Any) -> Any:
    async with _require_pool().acquire() as conn:
        return await conn.fetchval(query, *args)


async def ping() -> bool:
    try:
        return (await fetchval("SELECT 1")) == 1
    except Exception as exc:
        logger.warning("DB ping failed: %s", exc)
        return False
