"""
ARQ worker entrypoint — the ONE and only job queue in the system (never add a second).
Runs CV extraction + embedding off the request path (step 1.6); the DB pool is initialised
once at worker startup (separate process from the FastAPI app, so it needs its own pool)
and closed on shutdown. Restart the worker after task-code changes (see docker compose).
"""
from __future__ import annotations

from arq.connections import RedisSettings
from core.logging import configure_logging, get_logger
from db.session import close_pool, init_pool

from core.config import settings
from services.profile_ingest import run_ingest

logger = get_logger(__name__)


async def startup(ctx: dict) -> None:
    configure_logging()
    await init_pool()
    logger.info("ARQ worker started.")


async def shutdown(ctx: dict) -> None:
    await close_pool()
    logger.info("ARQ worker stopped.")


async def healthcheck_task(ctx: dict) -> str:
    """Trivial task proving the queue round-trips."""
    return "ok"


class WorkerSettings:
    functions = [healthcheck_task, run_ingest]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)