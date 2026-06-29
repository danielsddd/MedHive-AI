"""m3 — HNSW cosine indexes on embedding columns.

Builds sub-linear approximate-nearest-neighbour indexes (m=16, ef_construction=64,
vector_cosine_ops) so /match and /grants meet REQ-2 (<3s p95 over >=1,000 profiles).
Covers the active profiles.embedding, the mpnet experiment column, and grants.embedding.
Experiment columns gemini/biolord are indexed in Phase 3 when those experiments run.

Revision ID: m3_hnsw_indexes
Revises: m2_tables
"""
from alembic import op

revision = "m3_hnsw_indexes"
down_revision = "m2_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX profiles_embedding_hnsw
            ON profiles USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);

        CREATE INDEX profiles_embedding_mpnet_hnsw
            ON profiles USING hnsw (embedding_mpnet vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);

        CREATE INDEX grants_embedding_hnsw
            ON grants USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS grants_embedding_hnsw;
        DROP INDEX IF EXISTS profiles_embedding_mpnet_hnsw;
        DROP INDEX IF EXISTS profiles_embedding_hnsw;
        """
    )
