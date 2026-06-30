"""m1 — pgvector extension + local Supabase-compatible auth shim.

Enables the vector type and creates a minimal `auth` schema (auth.users + auth.uid())
so the same RLS policies that run on hosted Supabase also apply cleanly on the local
pgvector Postgres that powers the demo. auth.uid() reads the JWT subject from a session
GUC, exactly mirroring Supabase semantics.

Each DDL statement is its own op.execute() call — asyncpg's prepared-statement protocol
rejects multiple SQL commands in a single execute(), so one statement per call is required.

Revision ID: m1_extension
Revises:
"""
from alembic import op

revision = "m1_extension"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
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
    op.execute(
        """
        CREATE OR REPLACE FUNCTION auth.uid() RETURNS uuid
        LANGUAGE sql STABLE AS $$
            SELECT NULLIF(current_setting('request.jwt.claim.sub', true), '')::uuid
        $$
        """
    )


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS auth.uid()")
    op.execute("DROP TABLE IF EXISTS auth.users")
    op.execute("DROP SCHEMA IF EXISTS auth CASCADE")
    # Extensions are left in place intentionally (other DBs may share them).