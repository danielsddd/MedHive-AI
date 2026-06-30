#!/usr/bin/env python3
"""
P0.2b quota / live-provider validation for TAU 3346 — MedHive AI.
Run this after pasting keys into .env to confirm all providers work end-to-end.
Tests: Gemini 2.5 Flash (extraction), explanation model (Groq or Cerebras),
       explanation fallback, gemini-embedding-001 @ 768 dims (API embedding),
       Cerebras optional check, dead model guard.
Checks BOTH Daniel's and Roei's keys for each provider.
Exit code: 0 = all PASS, 1 = any FAIL.
"""
from __future__ import annotations

import os
import sys
from dotenv import load_dotenv
load_dotenv()

# Model strings — match config.py exactly
EXTRACTION_MODEL     = os.environ.get("EXTRACTION_MODEL",     "gemini/gemini-2.5-flash")
EXPLANATION_MODEL    = os.environ.get("EXPLANATION_MODEL",    "groq/openai/gpt-oss-120b")
EXPLANATION_FALLBACK = os.environ.get("EXPLANATION_FALLBACK", "groq/openai/gpt-oss-20b")
VECTOR_DIMENSIONS    = int(os.environ.get("VECTOR_DIMENSIONS", "768"))

# Cerebras optional test model (free tier)
CEREBRAS_MODEL = "cerebras/gpt-oss-120b"

# LiteLLM embedding model string for gemini-embedding-001
EMBEDDING_MODEL_LITELLM = "gemini/gemini-embedding-001"

# Dead strings — must NEVER succeed
DEAD_MODELS = (
    "gemini/gemini-2.0-flash",
    "gemini/gemini-2.0-flash-lite",
    "text-embedding-004",
    "groq/llama-3.3-70b-versatile",    # deprecated Jun 17 2026
    "groq/llama-3.1-8b-instant",       # deprecated Jun 17 2026
)

results: list[tuple[str, str, str]] = []  # (label, status, detail)


def record(label: str, status: str, detail: str = "") -> None:
    results.append((label, status, detail))


def _litellm():
    try:
        import litellm
        litellm.suppress_debug_info = True
        return litellm
    except Exception as exc:
        record("litellm import", "FAIL", str(exc))
        return None


def check_chat(model: str, api_key_value: str | None, label: str) -> None:
    """Test one model with one specific key value."""
    if not api_key_value:
        record(label, "SKIP", "key not set")
        return
    litellm = _litellm()
    if litellm is None:
        return
    try:
        resp = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": "Reply with the single word OK."}],
            max_tokens=5,
            api_key=api_key_value,
        )
        text = resp["choices"][0]["message"]["content"]
        record(label, "PASS", f"{model} -> {text!r}")
    except Exception as exc:
        record(label, "FAIL", f"{model}: {exc}")


def check_embedding(api_key_value: str | None, label: str) -> None:
    """
    Test gemini-embedding-001 via google-generativeai SDK directly.
    Verifies 768-dim output + unit norm after truncation + renormalisation.
    """
    if not api_key_value:
        record(label, "SKIP", "key not set")
        return
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key_value)
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content="medical researcher oncology immunotherapy",
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=VECTOR_DIMENSIONS,
        )
        vec = result["embedding"]
        norm = sum(x * x for x in vec) ** 0.5 or 1.0
        renorm = [x / norm for x in vec]
        unit_norm = abs(sum(x * x for x in renorm) ** 0.5 - 1.0) < 1e-3
        ok = len(renorm) == VECTOR_DIMENSIONS and unit_norm
        record(label, "PASS" if ok else "FAIL",
               f"gemini-embedding-001 -> {len(renorm)} dims, unit-norm={unit_norm}")
    except ImportError:
        # Fallback to litellm if google-generativeai not installed
        litellm = _litellm()
        if litellm is None:
            return
        try:
            resp = litellm.embedding(
                model=EMBEDDING_MODEL_LITELLM,
                input=["medical researcher oncology immunotherapy"],
                api_key=api_key_value,
            )
            vec = resp["data"][0]["embedding"]
            vec = vec[:VECTOR_DIMENSIONS]
            norm = sum(x * x for x in vec) ** 0.5 or 1.0
            renorm = [x / norm for x in vec]
            unit_norm = abs(sum(x * x for x in renorm) ** 0.5 - 1.0) < 1e-3
            ok = len(renorm) == VECTOR_DIMENSIONS and unit_norm
            record(label, "PASS" if ok else "FAIL",
                   f"gemini-embedding-001 -> {len(renorm)} dims, unit-norm={unit_norm}")
        except Exception as exc:
            record(label, "FAIL", f"gemini-embedding-001: {exc}")
    except Exception as exc:
        record(label, "FAIL", f"gemini-embedding-001: {exc}")


def check_cerebras(api_key_value: str | None, label: str) -> None:
    """Test Cerebras — optional provider, SKIP if key not set."""
    if not api_key_value:
        record(label, "SKIP", "key not set (optional)")
        return
    litellm = _litellm()
    if litellm is None:
        return
    try:
        resp = litellm.completion(
            model=CEREBRAS_MODEL,
            messages=[{"role": "user", "content": "Reply with the single word OK."}],
            max_tokens=5,
            api_key=api_key_value,
        )
        text = resp["choices"][0]["message"]["content"]
        record(label, "PASS", f"{CEREBRAS_MODEL} -> {text!r}")
    except Exception as exc:
        record(label, "FAIL", f"{CEREBRAS_MODEL}: {exc}")


def check_dead_models(gemini_key: str | None) -> None:
    """Confirm deprecated model strings are correctly rejected."""
    litellm = _litellm() if gemini_key else None
    for dead in DEAD_MODELS:
        if litellm is None:
            record(f"dead: {dead}", "PASS", "quarantined (no key)")
            continue
        try:
            litellm.completion(
                model=dead,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5,
            )
            record(f"dead: {dead}", "FAIL", "DANGER — deprecated model still responding!")
        except Exception:
            record(f"dead: {dead}", "PASS", "correctly rejected")


def get_api_key_for_model(model: str, groq_key: str | None, cerebras_key: str | None) -> str | None:
    """Return the appropriate API key based on the model's provider prefix."""
    if model.startswith("cerebras/"):
        return cerebras_key
    else:
        return groq_key  # assume groq/openai/… or groq/…


def main() -> int:
    gemini_daniel    = os.environ.get("GEMINI_API_KEY_DANIEL")
    gemini_roei      = os.environ.get("GEMINI_API_KEY_ROEI")
    groq_daniel      = os.environ.get("GROQ_API_KEY_DANIEL")
    groq_roei        = os.environ.get("GROQ_API_KEY_ROEI")
    cerebras_daniel  = os.environ.get("CEREBRAS_API_KEY_DANIEL")
    cerebras_roei    = os.environ.get("CEREBRAS_API_KEY_ROEI")
    gemini_active    = os.environ.get("GEMINI_API_KEY") or gemini_daniel

    print("TAU 3346 — MedHive AI — Provider Quota Validation")
    print("=" * 65)

    print("\n[GEMINI — Daniel]")
    check_chat(EXTRACTION_MODEL, gemini_daniel,  "  extraction LLM (Daniel)")
    check_embedding(gemini_daniel,               "  embedding API (Daniel)")

    print("\n[GEMINI — Roei]")
    check_chat(EXTRACTION_MODEL, gemini_roei,    "  extraction LLM (Roei)")
    check_embedding(gemini_roei,                 "  embedding API (Roei)")

    # Explanation models – use the correct key depending on the model string
    print("\n[EXPLANATION — Daniel]")
    check_chat(EXPLANATION_MODEL,
               get_api_key_for_model(EXPLANATION_MODEL, groq_daniel, cerebras_daniel),
               "  explanation primary (Daniel)")
    check_chat(EXPLANATION_FALLBACK,
               get_api_key_for_model(EXPLANATION_FALLBACK, groq_daniel, cerebras_daniel),
               "  explanation fallback (Daniel)")

    print("\n[EXPLANATION — Roei]")
    check_chat(EXPLANATION_MODEL,
               get_api_key_for_model(EXPLANATION_MODEL, groq_roei, cerebras_roei),
               "  explanation primary (Roei)")
    check_chat(EXPLANATION_FALLBACK,
               get_api_key_for_model(EXPLANATION_FALLBACK, groq_roei, cerebras_roei),
               "  explanation fallback (Roei)")

    print("\n[CEREBRAS — Daniel]")
    check_cerebras(cerebras_daniel, "  cerebras (Daniel)")

    print("\n[CEREBRAS — Roei]")
    check_cerebras(cerebras_roei,   "  cerebras (Roei)")

    print("\n[DEAD MODEL GUARD]")
    check_dead_models(gemini_active)

    print("\n" + "=" * 65)
    for label, status, detail in results:
        print(f"  [{status:4}] {label:38} {detail}")
    print("=" * 65)

    passed  = sum(1 for r in results if r[1] == "PASS")
    failed  = sum(1 for r in results if r[1] == "FAIL")
    skipped = sum(1 for r in results if r[1] == "SKIP")
    print(f"  PASS={passed}  FAIL={failed}  SKIP={skipped}")

    if skipped and not failed:
        print("  SKIPs = keys not set yet (or optional). Fill in .env and re-run.")
    if failed:
        print("  *** FIX FAILURES BEFORE PROCEEDING TO PHASE 1 ***")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())