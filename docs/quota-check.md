# Provider Quota Check (P0.2b)

This is the one-time validation you run *after* pasting real API keys, to confirm the live
providers work and that the dead model strings stay quarantined. With no keys present every
check is skipped, so the script is safe to run in any environment.

## How to run
```bash
# From the repo root, with your keys in .env:
python scripts/validate_quotas.py
```
The script prints a PASS / FAIL / SKIP table and exits non-zero only on a real failure
(a live key is present but the call failed, or a dead model unexpectedly succeeded).

## What it validates
- **Extraction LLM** — `gemini/gemini-2.5-flash` responds (needs `GEMINI_API_KEY`).
- **Explanation LLM** — `groq/llama-3.3-70b-versatile` responds (needs `GROQ_API_KEY`).
- **API embedding** — `gemini-embedding-001` truncated to 768 dims and L2-renormalised to unit
  length (needs `GEMINI_API_KEY`).
- **Dead-model guard** — `gemini-2.0-flash`, `gemini-2.0-flash-lite`, and `text-embedding-004`
  must error. These strings must never appear anywhere in the codebase.

## Live model strings (as configured)
| Role | Model string | Key |
| --- | --- | --- |
| Extraction (primary) | `gemini/gemini-2.5-flash` | `GEMINI_API_KEY` |
| Extraction (fallback) | `groq/llama-3.3-70b-versatile` | `GROQ_API_KEY` |
| Explanation (primary) | `groq/llama-3.3-70b-versatile` | `GROQ_API_KEY` |
| Explanation (fallback) | `groq/llama-3.1-8b-instant` | `GROQ_API_KEY` |
| Embedding (local, default) | `all-mpnet-base-v2` | none (self-hosted) |
| Embedding (API) | `gemini-embedding-001` | `GEMINI_API_KEY` |

## Rate caps
Keep self-imposed caps at or below ~50% of each provider's real limit. Configured in `.env`:
- `INGEST_PER_HOUR` (default 3) — CV ingestion jobs per user per hour.
- `EXPLAIN_PER_MIN` (default 10) — match-explanation LLM calls per minute.
- `MATCH_PER_MIN` (default 30) — matching queries per minute.

If a provider returns a rate-limit error, the gateway falls back to the configured fallback
model before surfacing `rate_limit_exceeded` to the client.
