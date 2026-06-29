"""m2 — core tables with vector(768) columns.

Creates every domain table from the schema (institutions, user_roles, profiles, ideas,
grants, matches, job_status, audit_logs). The profiles table carries the active embedding
plus separate experiment columns and the QC fields (sub_domain, sub_cluster, source,
openalex_id) required by the Phase 0 gate. All embeddings are fixed at vector(768).

Revision ID: m2_tables
Revises: m1_extension
"""
from alembic import op

revision = "m2_tables"
down_revision = "m1_extension"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE user_roles (
            user_id    UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
            role       TEXT NOT NULL DEFAULT 'researcher',
            created_at TIMESTAMPTZ DEFAULT now()
        );

        CREATE TABLE institutions (
            id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name       TEXT NOT NULL,
            department TEXT,
            country    TEXT,
            created_at TIMESTAMPTZ DEFAULT now()
        );

        CREATE TABLE profiles (
            id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id                UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
            full_name              TEXT,
            expertise_areas        TEXT[],
            methodological_skills  TEXT[],
            keywords               TEXT[],
            mesh_tags              TEXT[],
            summary                TEXT,
            education              TEXT[],
            notable_publications   TEXT[],
            affiliation_id         UUID REFERENCES institutions(id),
            embedding              VECTOR(768),
            embedding_mpnet        VECTOR(768),
            embedding_gemini       VECTOR(768),
            embedding_biolord      VECTOR(768),
            embedding_model_ver    TEXT,
            embedding_pending      BOOLEAN DEFAULT false,
            status                 TEXT DEFAULT 'active',
            confidence             FLOAT,
            sub_domain             TEXT,
            sub_cluster            TEXT,
            source                 TEXT DEFAULT 'cv',
            openalex_id            TEXT,
            created_at             TIMESTAMPTZ DEFAULT now(),
            updated_at             TIMESTAMPTZ DEFAULT now(),
            UNIQUE (user_id)
        );

        CREATE TABLE ideas (
            id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id    UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
            title      TEXT NOT NULL,
            abstract   TEXT NOT NULL,
            tags       TEXT[],
            embedding  VECTOR(768),
            created_at TIMESTAMPTZ DEFAULT now()
        );

        CREATE TABLE grants (
            id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            agency           TEXT NOT NULL,
            title            TEXT NOT NULL,
            description      TEXT,
            deadline         DATE,
            keywords         TEXT[],
            eligibility_text TEXT,
            sub_domain       TEXT,
            embedding        VECTOR(768),
            source           TEXT DEFAULT 'seed',
            created_at       TIMESTAMPTZ DEFAULT now()
        );

        CREATE TABLE matches (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            query_user_id   UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
            result_user_id  UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
            cosine_score    FLOAT,
            tag_overlap     FLOAT,
            proximity_score FLOAT,
            final_score     FLOAT,
            explanation     TEXT,
            created_at      TIMESTAMPTZ DEFAULT now()
        );

        CREATE TABLE job_status (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_type      TEXT NOT NULL,
            status        TEXT NOT NULL DEFAULT 'queued',
            user_id       UUID REFERENCES auth.users(id) ON DELETE CASCADE,
            profile_id    UUID,
            error_code    TEXT,
            error_message TEXT,
            created_at    TIMESTAMPTZ DEFAULT now(),
            updated_at    TIMESTAMPTZ DEFAULT now()
        );

        CREATE TABLE audit_logs (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            actor_id    UUID,
            action      TEXT NOT NULL,
            entity_type TEXT,
            entity_id   UUID,
            payload     JSONB,
            created_at  TIMESTAMPTZ DEFAULT now()
        );
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS audit_logs;
        DROP TABLE IF EXISTS job_status;
        DROP TABLE IF EXISTS matches;
        DROP TABLE IF EXISTS grants;
        DROP TABLE IF EXISTS ideas;
        DROP TABLE IF EXISTS profiles;
        DROP TABLE IF EXISTS institutions;
        DROP TABLE IF EXISTS user_roles;
        """
    )
