"""
Alembic async migration runner. Pulls the database URL from core.config (never from
alembic.ini) so secrets live only in .env, and drives migrations over an async engine via
asyncpg with run_sync. Migrations here are raw SQL (op.execute), so no ORM metadata is
needed; target_metadata stays None. Supports both online and offline modes.
"""
from __future__ import annotations

import asyncio

from alembic import context
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from core.config import settings  # noqa: E402

target_metadata = None
DB_URL = settings.DATABASE_URL


def run_migrations_offline() -> None:
    context.configure(url=DB_URL, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_async_engine(DB_URL, pool_pre_ping=True)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
