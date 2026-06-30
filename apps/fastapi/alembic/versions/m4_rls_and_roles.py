"""m4 — RLS policies, least-privilege roles, and the matching SECURITY DEFINER function.

Enables (and FORCEs) row-level security so researchers touch only their own rows, using
the Supabase performance pattern (select auth.uid()) so the function is evaluated once,
not per row. Creates NOLOGIN privilege roles (authenticated, matching_read) the runtime
SETs into, and search_profiles() — a SECURITY DEFINER function that is the ONLY sanctioned
way to run cross-profile vector search, so /match never needs the service-role key.

Each DDL statement is its own op.execute() call — asyncpg's prepared-statement protocol
rejects multiple SQL commands in a single execute(). A DO $$ ... END $$ block counts as
ONE statement, but anything after it in the same string is a second statement and will
break, so each GRANT/CREATE POLICY/ALTER TABLE is split out individually.

Revision ID: m4_rls_and_roles
Revises: m3_hnsw_indexes
"""
from alembic import op

revision = "m4_rls_and_roles"
down_revision = "m3_hnsw_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Idempotent role creation (Postgres has no CREATE ROLE IF NOT EXISTS).
    # The DO $$ ... END $$ block is one statement on its own — fine as a single execute().
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
                CREATE ROLE authenticated NOLOGIN;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'matching_read') THEN
                CREATE ROLE matching_read NOLOGIN;
            END IF;
        END $$;
        """
    )

    # Per-user RLS on owned tables. Policies target the authenticated role and compare to
    # the JWT subject via a cached subselect. Each statement is its own execute() call.
    for table in ("profiles", "ideas"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
        op.execute(
            f"""
            CREATE POLICY {table}_own_select ON {table}
                FOR SELECT TO authenticated USING ((select auth.uid()) = user_id);
            """
        )
        op.execute(
            f"""
            CREATE POLICY {table}_own_insert ON {table}
                FOR INSERT TO authenticated WITH CHECK ((select auth.uid()) = user_id);
            """
        )
        op.execute(
            f"""
            CREATE POLICY {table}_own_update ON {table}
                FOR UPDATE TO authenticated USING ((select auth.uid()) = user_id)
                WITH CHECK ((select auth.uid()) = user_id);
            """
        )
        op.execute(
            f"""
            CREATE POLICY {table}_own_delete ON {table}
                FOR DELETE TO authenticated USING ((select auth.uid()) = user_id);
            """
        )
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO authenticated;")

    # user_roles: a user can read only their own role row.
    op.execute("ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE user_roles FORCE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY user_roles_own_select ON user_roles
            FOR SELECT TO authenticated USING ((select auth.uid()) = user_id);
        """
    )
    op.execute("GRANT SELECT ON user_roles TO authenticated;")

    # grants: public read for any authenticated user; writes are admin/service-role only.
    op.execute("ALTER TABLE grants ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE grants FORCE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY grants_public_read ON grants
            FOR SELECT TO authenticated USING (true);
        """
    )
    op.execute("GRANT SELECT ON grants TO authenticated;")

    # Cross-profile vector search: SECURITY DEFINER bypasses RLS for THIS function only.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION search_profiles(
            query_embedding VECTOR(768),
            k               INT DEFAULT 10,
            exclude_user    UUID DEFAULT NULL
        )
        RETURNS TABLE(profile_id UUID, user_id UUID, score FLOAT)
        LANGUAGE SQL
        SECURITY DEFINER
        SET search_path = public, extensions
        AS $$
            SELECT id, user_id, 1 - (embedding <=> query_embedding) AS score
            FROM profiles
            WHERE user_id != COALESCE(exclude_user,
                                      '00000000-0000-0000-0000-000000000000')
              AND embedding IS NOT NULL
            ORDER BY embedding <=> query_embedding
            LIMIT k;
        $$;
        """
    )
    op.execute("REVOKE ALL ON FUNCTION search_profiles(VECTOR, INT, UUID) FROM PUBLIC;")
    op.execute("GRANT EXECUTE ON FUNCTION search_profiles(VECTOR, INT, UUID) TO matching_read;")


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS search_profiles(VECTOR, INT, UUID)")
    for table in ("profiles", "ideas"):
        op.execute(f"DROP POLICY IF EXISTS {table}_own_select ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_own_insert ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_own_update ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_own_delete ON {table};")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    op.execute("DROP POLICY IF EXISTS user_roles_own_select ON user_roles;")
    op.execute("ALTER TABLE user_roles NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE user_roles DISABLE ROW LEVEL SECURITY;")
    op.execute("DROP POLICY IF EXISTS grants_public_read ON grants;")
    op.execute("ALTER TABLE grants NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE grants DISABLE ROW LEVEL SECURITY;")
    # Roles are left in place (other migrations/objects may depend on them).