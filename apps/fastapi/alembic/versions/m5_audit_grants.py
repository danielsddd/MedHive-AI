"""m5 — audit_logs INSERT-only grant for the app writer role.

Creates the NOLOGIN app_writer role and grants it INSERT on audit_logs and nothing else —
no UPDATE, no DELETE — making the audit trail immutable in practice at the database level.
This is the final migration; running `alembic downgrade base && alembic upgrade head` must
reproduce an identical schema.

Each DDL statement is its own op.execute() call — asyncpg's prepared-statement protocol
rejects multiple SQL commands in a single execute(). The DO $$ ... END $$ block is one
statement on its own; the REVOKE/GRANT that follow it are split into separate calls.

Revision ID: m5_audit_grants
Revises: m4_rls_and_roles
"""
from alembic import op

revision = "m5_audit_grants"
down_revision = "m4_rls_and_roles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_writer') THEN
                CREATE ROLE app_writer NOLOGIN;
            END IF;
        END $$;
        """
    )
    # INSERT only. Deliberately NO UPDATE and NO DELETE grants, ever.
    op.execute("REVOKE ALL ON audit_logs FROM app_writer;")
    op.execute("GRANT INSERT ON audit_logs TO app_writer;")


def downgrade() -> None:
    op.execute("REVOKE INSERT ON audit_logs FROM app_writer")
    # app_writer role left in place intentionally.