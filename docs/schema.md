# Database Schema — TAU 3346

Authoritative source is the Alembic migrations in `apps/fastapi/alembic/versions/`
(`m1`→`m5`, applied in strict order). This document is a human-readable mirror; if it ever
disagrees with the migrations, the migrations win.

## Migration order
1. `m1_extension` — `vector` + `pgcrypto` extensions; local `auth` schema shim (`auth.users`,
   `auth.uid()`) so the same RLS runs against the local pgvector container.
2. `m2_tables` — all application tables.
3. `m3_hnsw_indexes` — HNSW cosine indexes (`m=16`, `ef_construction=64`).
4. `m4_rls_and_roles` — roles, RLS enable+force, policies, `search_profiles()` function.
5. `m5_audit_grants` — INSERT-only grant on `audit_logs`.

## Tables

### user_roles
RBAC mapping. `user_id` (PK, FK→auth.users), `role` (default `researcher`), `created_at`.

### institutions
`id` (PK), `name`, `department`, `country`, `created_at`.

### profiles
One row per researcher (`UNIQUE(user_id)`). Structured profile fields
(`full_name`, `expertise_areas[]`, `methodological_skills[]`, `keywords[]`, `mesh_tags[]`,
`summary`, `education[]`, `notable_publications[]`, `affiliation_id`→institutions).
Embeddings — all `VECTOR(768)`: `embedding` (active), `embedding_mpnet`, `embedding_gemini`,
`embedding_biolord` (experiment columns). Bookkeeping: `embedding_model_ver`,
`embedding_pending`, `status` (default `active`), `confidence`. QC/provenance:
`sub_domain`, `sub_cluster`, `source` (default `cv`), `openalex_id`. Timestamps
`created_at`, `updated_at`.

### ideas
Research ideas. `id`, `user_id`, `title`, `abstract`, `tags[]`, `embedding VECTOR(768)`,
`created_at`. (Endpoint logic lands in Phase 5.)

### grants
Funding opportunities. `id`, `agency`, `title`, `description`, `deadline`, `keywords[]`,
`eligibility_text`, `sub_domain`, `embedding VECTOR(768)`, `source` (default `seed`),
`created_at`. Seeded from `data/grants_seed.json`. (Endpoint logic lands in Phase 4.)

### matches
Computed collaboration matches. `id`, `query_user_id`, `result_user_id`, component scores
(`cosine_score`, `tag_overlap`, `proximity_score`, `final_score`), `explanation`, `created_at`.

### job_status
Async job tracking. `id`, `job_type`, `status` (default `queued`), `user_id`, `profile_id`,
`error_code`, `error_message`, `created_at`, `updated_at`.

### audit_logs
Immutable, INSERT-only. `id`, `actor_id`, `action`, `entity_type`, `entity_id`,
`payload JSONB`, `created_at`. The app role has no UPDATE/DELETE grant.

## Row-Level Security
RLS is `ENABLE`d and `FORCE`d on `profiles`, `ideas`, and `user_roles`. Policies use
`(select auth.uid())` (wrapped for planner performance). `grants` is public-read.
`search_profiles(query_embedding vector(768), k, exclude_user)` is `SECURITY DEFINER`,
returns cosine similarity `1 - (embedding <=> q)`, and `EXECUTE` is granted only to the
`matching_read` role.

## Indexes
HNSW cosine indexes on `profiles.embedding`, `profiles.embedding_mpnet`, and `grants.embedding`.
