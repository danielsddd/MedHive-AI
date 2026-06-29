"""
ARQ worker entrypoint — the ONE and only job queue in the system (never add a second).
Runs CV extraction + embedding off the request path in Phase 1; this scaffold wires the
worker, Redis settings, and startup/shutdown hooks so the container runs green now and
tasks are added later. Restart the worker after task-code changes (see docker compose).
"""
from __future__ import annotations

from arq.connections import RedisSettings

from core.config import settings
from core.logging import configure_logging, get_logger

logger = get_logger(__name__)


async def startup(ctx: dict) -> None:
    configure_logging()
    logger.info("ARQ worker started.")


async def shutdown(ctx: dict) -> None:
    logger.info("ARQ worker stopped.")


async def healthcheck_task(ctx: dict) -> str:
    """Trivial task proving the queue round-trips; replaced by real ingest tasks in Phase 1."""
    return "ok"


class WorkerSettings:
    functions = [healthcheck_task]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
