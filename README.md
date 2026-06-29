# MedCollab — TAU Project 3346

**AI-Based Platform for Medical Research Collaboration.**
Tel Aviv University · Daniel Simanovsky & Roei Ben Artzi.

This repository is the **Phase 0 foundation**: a runnable monorepo (FastAPI backend +
Next.js frontend + Postgres/pgvector + Redis) that **boots with zero API keys**. Everything
degrades gracefully to deterministic offline stubs, so you can run, test, and demo before
touching a single provider. Dropping a real key into `.env` flips a subsystem to live **with no
code change**.

---

## 1. Quick start (no keys, no accounts)

### Option A — Docker (recommended; nothing to install locally except Docker)
```bash
cp .env.example .env          # leave it as-is to run fully offline
pnpm dev                      # == docker compose -f docker-compose.dev.yml up --build
```
Then open:
- Frontend: http://localhost:3000
- Backend docs: http://localhost:8000/docs
- Health: http://localhost:8000/healthz

Check everything is wired:
```bash
pnpm health                   # PASS/FAIL table for Postgres, Redis, FastAPI deps
```

### Option B — Backend only, no Docker
```bash
cd apps/fastapi
pip install poetry && poetry install --no-root
poetry run pytest -q          # 10 offline tests should pass
poetry run uvicorn main:app --reload
```

In offline mode: auth accepts any bearer token (returns a fixed dev user), embeddings use a
deterministic 768-dim stub, and the LLM gateway returns canned JSON. No network required.

---

## 2. How to add API keys (go live)

The entire swap mechanism is **`.env` only**. Open `.env` and:

1. Paste a key next to the matching variable:
   ```env
   GEMINI_API_KEY=your_key_here
   GROQ_API_KEY=your_key_here
   ```
2. Leave the `*_MODE` switches on `auto` (the default). `auto` means: **go live the moment a
   key is present, otherwise stay on the offline stub.** No code edit, no restart logic to
   remember.

That's it. To *force* a mode regardless of keys:
```env
LLM_MODE=auto         # auto | live | offline(dev)
EMBEDDING_MODE=auto   # auto | live | offline(dev)
AUTH_MODE=auto        # auto | live | dev
```

Validate live providers once after adding keys:
```bash
python scripts/validate_quotas.py     # PASS/FAIL/SKIP table; proves dead models error out
```

> The Supabase **service-role key** (`SUPABASE_SERVICE_ROLE_KEY`) is backend-only. It is never
> read by the frontend and never logged.

---

## 3. How to swap a provider or model

No code changes — edit the model string + key in `.env`:

| You want to change | Edit in `.env` | Also need |
| --- | --- | --- |
| Extraction LLM | `EXTRACTION_MODEL` / `EXTRACTION_FALLBACK` | the matching provider key |
| Explanation LLM | `EXPLANATION_MODEL` / `EXPLANATION_FALLBACK` | the matching provider key |
| Embeddings: local ↔ API | `EMBEDDING_MODEL_ACTIVE=local|api` | (api needs `GEMINI_API_KEY`) |
| Which embedding column is live | `ACTIVE_EMBEDDING_COLUMN` | — |

Model strings use LiteLLM's `provider/model` format (e.g. `gemini/gemini-2.5-flash`,
`groq/llama-3.3-70b-versatile`). LiteLLM reads provider keys by their standard env names — that
*is* the swap. Model names live only in config, never hard-coded in logic.

**Locked / forbidden:** `VECTOR_DIMENSIONS` stays `768`. Never use the dead strings
`gemini-2.0-flash`, `gemini-2.0-flash-lite`, or `text-embedding-004`.

---

## 4. Project structure
```
tau3346/
├─ apps/
│  ├─ fastapi/                 # ALL business logic lives here
│  │  ├─ core/                 # config (single source of truth), constants, errors, logging
│  │  ├─ db/                   # asyncpg pool + redis client
│  │  ├─ services/             # embedding, llm_gateway, auth, audit (provider seams)
│  │  ├─ schemas/              # pydantic contracts (locked ResearcherProfile)
│  │  ├─ routers/              # health, auth (more added per phase)
│  │  ├─ alembic/versions/     # migrations m1→m5 (strict order)
│  │  ├─ tests/                # offline test suite
│  │  ├─ main.py  worker.py    # API app + ARQ worker
│  │  └─ pyproject.toml  Dockerfile
│  └─ nextjs/                  # auth/session glue ONLY — no business API routes
│     ├─ app/(public)/         # login, register, reset-password
│     ├─ app/(app)/            # protected shell + home dashboard
│     ├─ components/  hooks/  lib/   middleware.ts
│     └─ package.json  Dockerfile
├─ packages/types/            # shared TS/Py contracts (VECTOR_DIMENSIONS, ResearcherProfile)
├─ scripts/                   # healthcheck, download_models, validate_quotas
├─ data/grants_seed.json      # immutable seed grants (REQ-3 floor)
├─ docs/                      # ADR, schema, quota-check, annotation rubric
├─ docker-compose.dev.yml     # self-hosted pgvector + redis + fastapi + arq-worker + nextjs
├─ docker-compose.prod.yml
└─ .env.example               # copy to .env — the only file you edit to add keys
```

---

## 5. Architecture rules (the short version)
- **FastAPI owns all business logic.** Next.js only does auth/session + UI.
- **One queue** (ARQ over Redis). **One vector store** (pgvector). Width **locked at 768**.
- **Self-hosted embeddings by default** (`all-mpnet-base-v2`); profile text stays on our infra.
- **Stable errors** everywhere: `{"code","message"}`, no stack traces.
- **Immutable audit log**: every mutation is recorded; `audit_logs` is INSERT-only.
See `docs/ADR.md` for the full decision log and `docs/schema.md` for the data model.

---

## 6. Common commands
```bash
pnpm dev          # full stack (Docker)
pnpm down         # stop the stack
pnpm health       # service health table
pnpm models       # pre-pull embedding models into the HF cache (optional)
pnpm lint         # Biome (frontend)
# backend:
cd apps/fastapi && poetry run pytest -q
cd apps/fastapi && poetry run alembic upgrade head     # apply migrations m1→m5
```

---

## 7. What's intentionally deferred
Phase 0 ships foundations only. The following arrive in later phases and are stubbed or absent
for now: profile ingestion (P1), embeddings/indexing pipeline (P2), matching incl. complementary
scoring (P3), grant matching endpoints (P4), research-idea endpoints (P5), plus
Sentry/PostHog/k6/LlamaIndex (later). The nav links for those pages exist but their backends are
not yet implemented.
