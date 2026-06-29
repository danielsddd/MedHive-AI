# Alembic Migrations — strict order (never reorder)

```
m1_extension     CREATE EXTENSION vector + local Supabase auth shim (auth.users, auth.uid())
m2_tables        all core tables with vector(768) columns
m3_hnsw_indexes  HNSW cosine indexes for ANN search
m4_rls_and_roles RLS policies + authenticated/matching_read roles + search_profiles()
m5_audit_grants  audit_logs INSERT-only grant for app_writer
```

Apply:    `alembic upgrade head`
Reset:    `alembic downgrade base`
Verify:   `alembic downgrade base && alembic upgrade head` must yield an identical schema.
