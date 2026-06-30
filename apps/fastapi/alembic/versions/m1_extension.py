"""m1 — pgvector extension + local Supabase-compatible auth shim.

Enables the vector type and, ONLY on a local/non-Supabase Postgres, creates a minimal
`auth` schema (auth.users + auth.uid()) so the same RLS policies that run on hosted
Supabase also apply cleanly during local development. On a REAL Supabase project,
`auth.users` and `auth.uid()` already exist natively (owned by Supabase's internal
supabase_auth_admin role) — this migration detects that and skips the shim entirely,
since creating or altering anything in Supabase's real `auth` schema is both
unnecessary and will fail due to insufficient privileges.

A marker comment on the auth.users table (via COMMENT ON) records whether THIS
migration created the shim, so downgrade() only ever drops what it built — it never
touches a pre-existing real Supabase auth schema, even when run a second time.

Each DDL statement is its own op.execute() call — asyncpg's prepared-statement protocol
rejects multiple SQL commands in a single execute(), so one statement per call is required.
Raw introspection queries use sqlalchemy.text() — modern SQLAlchemy refuses to execute a
bare Python string via conn.execute().

Revision ID: m1_extension
Revises:
"""
from sqlalchemy import text

from alembic import op

revision = "m1_extension"
down_revision = None
branch_labels = None
depends_on = None

_SHIM_MARKER = "tau3346_local_auth_shim"


def _auth_users_already_exists() -> bool:
    """True if auth.users already exists for ANY reason (real Supabase or a prior run)."""
    conn = op.get_bind()
    result = conn.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'auth' AND table_name = 'users'
            )
            """
        )
    )
    return bool(result.scalar())


def _shim_was_created_by_this_migration() -> bool:
    """True only if auth.users exists AND carries our marker comment (i.e. we built it)."""
    conn = op.get_bind()
    result = conn.execute(text("SELECT obj_description('auth.users'::regclass, 'pg_class')"))
    comment = result.scalar()
    return comment == _SHIM_MARKER


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    if _auth_users_already_exists():
        # Real Supabase project (or shim already built) — auth.users / auth.uid() are
        # already there. Do not create, alter, or touch anything in this schema.
        return

    # Local/non-Supabase Postgres — build the minimal compatible shim and mark it as ours.
    op.execute("CREATE SCHEMA IF NOT EXISTS auth")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS auth.users (
            id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email      TEXT,
            created_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute(f"COMMENT ON TABLE auth.users IS '{_SHIM_MARKER}'")
    op.execute(
        """
        CREATE OR REPLACE FUNCTION auth.uid() RETURNS uuid
        LANGUAGE sql STABLE AS $$
            SELECT NULLIF(current_setting('request.jwt.claim.sub', true), '')::uuid
        $$
        """
    )


def downgrade() -> None:
    if not _auth_users_already_exists() or not _shim_was_created_by_this_migration():
        # Either nothing to drop, or this is real Supabase's auth schema — never touch it.
        return
    op.execute("DROP FUNCTION IF EXISTS auth.uid()")
    op.execute("DROP TABLE IF EXISTS auth.users")
    op.execute("DROP SCHEMA IF EXISTS auth CASCADE")
    # Extensions are left in place intentionally (other DBs may share them).