"""
Self-hosted embedding service — the ONLY place that turns text into a 768-dim vector for
the local path, so profile text never leaves our infrastructure (hard rule). Loads
all-mpnet-base-v2 from the pre-pulled HF cache as a singleton, L2-normalises every output
so cosine == dot product, and exposes build_embedding_input() as the single source of
truth for embed text. If the ML stack/model is unavailable it falls back to a deterministic
stub vector so the app, dimension guard, and tests still run with zero setup.
"""
from __future__ import annotations

import hashlib

import numpy as np

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)

_model = None          # lazy SentenceTransformer singleton
_stub_active = False   # True once we have fallen back to the stub encoder


def _try_load_model():
    """Load the local SentenceTransformer once. Returns None if unavailable (-> stub)."""
    global _model, _stub_active
    if _model is not None:
        return _model
    try:
        from sentence_transformers import SentenceTransformer  # heavy import, done lazily

        _model = SentenceTransformer(settings.EMBEDDING_MODEL_LOCAL)
        logger.info("Loaded embedding model: %s", settings.EMBEDDING_MODEL_LOCAL)
        return _model
    except Exception as exc:  # model not cached / torch missing -> stub
        _stub_active = True
        logger.warning(
            "Local embedding model unavailable (%s). Using deterministic STUB encoder "
            "(dev only — vectors are not semantically meaningful).", exc,
        )
        return None


def _stub_vector(text: str) -> np.ndarray:
    """Deterministic, reproducible pseudo-embedding seeded from the text hash."""
    seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16) % (2**32)
    rng = np.random.default_rng(seed)
    return rng.standard_normal(settings.VECTOR_DIMENSIONS).astype(np.float32)


def embed_text(text: str) -> np.ndarray:
    """Return a VECTOR_DIMENSIONS-length, L2-normalised float32 embedding."""
    model = _try_load_model()
    if model is not None:
        vec = np.asarray(model.encode(text, normalize_embeddings=True), dtype=np.float32)
    else:
        vec = _stub_vector(text)
    norm = float(np.linalg.norm(vec))
    if norm > 0:
        vec = vec / norm
    return vec.astype(np.float32)


def embed_batch(texts: list[str]) -> list[np.ndarray]:
    return [embed_text(t) for t in texts]


def is_stub() -> bool:
    """True when the stub encoder is in use (surfaced by /healthz for transparency)."""
    return _stub_active


def build_embedding_input(profile) -> str:
    """
    Single source of truth for embedding input — used for first ingest AND every re-embed.
    Accepts any object exposing expertise_areas, methodological_skills, summary.
    """
    return (
        f"EXPERTISE: {'; '.join(profile.expertise_areas)}; "
        f"SKILLS: {'; '.join(profile.methodological_skills)}; "
        f"SUMMARY: {profile.summary}"
    )
