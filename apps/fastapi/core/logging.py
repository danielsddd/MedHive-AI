"""
Process-wide logging setup. Configures a single root handler at the level from config so
every module shares consistent, timestamped output. Import and call configure_logging()
once at app/worker startup. Never logs secrets (service-role key, API keys) — call sites
must pass redacted context only.
"""
import logging

from core.config import settings


def configure_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s %(levelname)-7s %(name)s :: %(message)s",
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
