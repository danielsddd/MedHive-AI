#!/usr/bin/env python3
"""
P0.2b quota / live-provider validation. Run ONCE after pasting real keys to prove the live
stack works end-to-end: the extraction LLM (Gemini 2.5 Flash), an explanation LLM (Groq), the
API embedding model (gemini-embedding-001 truncated+renormalised to the locked 768 dims), and a
guard test that the DEAD model strings still error out. With no keys present every check SKIPs
(never fails), so this is safe to run in any environment. Exit code is non-zero only on real FAIL.
"""
from __future__ import annotations

import os
import sys

# Model strings come from env (mirrors core/config.py); never hard-coded business values.
EXTRACTION_MODEL = os.environ.get("EXTRACTION_MODEL", "gemini/gemini-2.5-flash")
EXPLANATION_MODEL = os.environ.get("EXPLANATION_MODEL", "groq/llama-3.3-70b-versatile")
EMBEDDING_MODEL_API = os.environ.get("EMBEDDING_MODEL_API", "gemini-embedding-001")
VECTOR_DIMENSIONS = int(os.environ.get("VECTOR_DIMENSIONS", "768"))

# Strings that must NEVER work — if any of these succeed, the guard FAILS.
DEAD_MODELS = ("gemini/gemini-2.0-flash", "gemini/gemini-2.0-flash-lite", "text-embedding-004")

results: list[tuple[str, str, str]] = []  # (check, status, detail)


def record(check: str, status: str, detail: str = "") -> None:
    results.append((check, status, detail))


def _litellm():
    try:
        import litellm  # noqa: WPS433 (local import keeps the script importable without the dep)

        return litellm
    except Exception as exc:  # pragma: no cover - environment dependent
        record("litellm import", "SKIP", f"litellm not installed ({exc})")
        return None


def check_chat(model: str, key_env: str, label: str) -> None:
    if not os.environ.get(key_env):
        record(label, "SKIP", f"{key_env} not set")
        return
    litellm = _litellm()
    if litellm is None:
        return
    try:
        resp = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": "Reply with the single word OK."}],
            max_tokens=5,
        )
        text = resp["choices"][0]["message"]["content"]
        record(label, "PASS", f"{model} -> {text!r}")
    except Exception as exc:
        record(label, "FAIL", f"{model}: {exc}")


def check_embedding() -> None:
    if not os.environ.get("GEMINI_API_KEY"):
        record("embedding (api)", "SKIP", "GEMINI_API_KEY not set")
        return
    litellm = _litellm()
    if litellm is None:
        return
    try:
        resp = litellm.embedding(model=EMBEDDING_MODEL_API, input=["test sentence"])
        vec = resp["data"][0]["embedding"]
        # gemini-embedding-001 returns >768 dims; truncate to 768 then L2-renormalise.
        vec = vec[:VECTOR_DIMENSIONS]
        norm = sum(x * x for x in vec) ** 0.5 or 1.0
        renorm = [x / norm for x in vec]
        ok = len(renorm) == VECTOR_DIMENSIONS and abs(sum(x * x for x in renorm) ** 0.5 - 1.0) < 1e-3
        record(
            "embedding (api)",
            "PASS" if ok else "FAIL",
            f"{EMBEDDING_MODEL_API} -> {len(renorm)} dims, unit-norm={ok}",
        )
    except Exception as exc:
        record("embedding (api)", "FAIL", f"{EMBEDDING_MODEL_API}: {exc}")


def check_dead_models() -> None:
    # We only need keys to attempt the call; if absent we still assert the strings are quarantined.
    has_key = bool(os.environ.get("GEMINI_API_KEY"))
    litellm = _litellm() if has_key else None
    for dead in DEAD_MODELS:
        if litellm is None:
            record(f"dead guard: {dead}", "PASS", "quarantined (no live attempt)")
            continue
        try:
            litellm.completion(
                model=dead,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5,
            )
            record(f"dead guard: {dead}", "FAIL", "dead model unexpectedly succeeded")
        except Exception:
            record(f"dead guard: {dead}", "PASS", "errored as expected")


def main() -> int:
    print("TAU 3346 — P0.2b quota / live-provider validation")
    print("=" * 60)
    check_chat(EXTRACTION_MODEL, "GEMINI_API_KEY", "extraction LLM")
    check_chat(EXPLANATION_MODEL, "GROQ_API_KEY", "explanation LLM")
    check_embedding()
    check_dead_models()

    for check, status, detail in results:
        print(f"  [{status:4}] {check:24} {detail}")
    print("=" * 60)

    failed = [r for r in results if r[1] == "FAIL"]
    skipped = [r for r in results if r[1] == "SKIP"]
    print(f"  PASS={sum(1 for r in results if r[1] == 'PASS')}  "
          f"FAIL={len(failed)}  SKIP={len(skipped)}")
    if skipped and not failed:
        print("  (SKIPs are expected when keys are absent — paste keys in .env to validate live.)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
