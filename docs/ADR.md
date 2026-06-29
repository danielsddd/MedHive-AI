# Architecture Decision Records — TAU 3346

Short, append-only records of the binding technical decisions. Each entry is immutable once
merged; supersede with a new entry rather than editing an old one.

---

## ADR-001 — FastAPI owns all business logic; Next.js is glue only
**Status:** Accepted
**Decision:** All domain logic (extraction, embedding, matching, grants, ideas) lives in the
FastAPI service. Next.js handles only authentication/session and presentation. It exposes no
business API routes.
**Why:** One place to test, rate-limit, and audit. Avoids logic drift across two runtimes.

## ADR-002 — Vector width is locked at 768
**Status:** Accepted
**Decision:** Every embedding column is `VECTOR(768)`. A startup assertion refuses to boot on
mismatch. The API embedding model (gemini-embedding-001) is truncated and L2-renormalised to 768.
**Why:** Mixed dimensions silently corrupt cosine similarity. The lock is a hard rule.

## ADR-003 — One queue (ARQ), one vector store (pgvector)
**Status:** Accepted
**Decision:** ARQ over Redis is the only task queue; pgvector is the only vector store. No
Celery, no external vector DB.
**Why:** Minimise moving parts for a two-person team; keep everything self-hostable.

## ADR-004 — Self-hosted embeddings by default
**Status:** Accepted
**Decision:** Profile text is embedded locally with `all-mpnet-base-v2` (768d). The API model is
a comparison/fallback only. Profile text never leaves our infrastructure in the default path.
**Why:** Privacy of researcher data and cost control.

## ADR-005 — Graceful offline mode (no keys required to run)
**Status:** Accepted
**Decision:** `LLM_MODE`, `EMBEDDING_MODE`, and `AUTH_MODE` each support `auto|live|offline(dev)`.
In `auto`, a subsystem goes live iff its key is present, else it uses a deterministic stub.
**Why:** The project must boot, test, and demo with zero setup; adding a key flips to live with
no code change.

## ADR-006 — Stable error contract
**Status:** Accepted
**Decision:** Every error is `{"code": "STABLE_CODE", "message": "..."}`. Codes are frozen once
shipped. No stack traces reach the client. The frontend maps codes to friendly copy.
**Why:** Predictable UX and a stable contract the frontend can depend on.

## ADR-007 — Immutable, INSERT-only audit log
**Status:** Accepted
**Decision:** Every mutation writes to `audit_logs`. The app role has INSERT only — no UPDATE or
DELETE grant on that table.
**Why:** Tamper-evident provenance for a research-integrity system.

## ADR-008 — PyMuPDF + pdfplumber for parsing
**Status:** Accepted
**Decision:** CV/PDF parsing uses PyMuPDF and pdfplumber. Unstructured.io is not used.
**Why:** Lighter dependency footprint and predictable behaviour on academic CVs.

## ADR-009 — Biome as the single TS/JS linter+formatter
**Status:** Accepted
**Decision:** Biome replaces ESLint + Prettier on the frontend; Next's ESLint is disabled during
builds.
**Why:** One tool, no fix-on-save conflicts.
