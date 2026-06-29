#!/usr/bin/env bash
# Pre-pulls the self-hosted embedding models into the HuggingFace cache so containers never
# download at boot (faster, offline-friendly demos). Pulls the active 768-dim model and the
# biomedical comparison model used in EXP-i+. Safe to re-run; HF caches are content-addressed.
# Override the cache location with HF_HOME (defaults to the compose `hf_cache` volume path).
set -euo pipefail

export HF_HOME="${HF_HOME:-/hf_cache}"
echo "Downloading embedding models into HF_HOME=${HF_HOME} ..."

python - <<'PY'
import os
os.environ.setdefault("HF_HOME", "/hf_cache")
from sentence_transformers import SentenceTransformer

MODELS = [
    "all-mpnet-base-v2",          # active 768-dim production model
    "FremyCompany/BioLORD-2023",  # biomedical comparison (EXP-i+)
]
for name in MODELS:
    print(f"  -> {name}")
    SentenceTransformer(name)     # downloads + caches; we don't keep the handle
print("Done.")
PY
