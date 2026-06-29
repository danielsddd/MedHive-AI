"""
Embedding service — the ONLY place that turns text into a 768-dim vector. Two paths:
  local (default): all-mpnet-base-v2 via SentenceTransformer, self-hosted, profile text
                   never leaves our infrastructure (hard rule).
  api:             gemini-embedding-001, truncated + L2-renormalised to 768 dims (MRL output).
L2-normalises every output so cosine == dot product. Keys are required — no offline stubs.
Raises APIError with stable code on failure so the frontend always gets a clean message.
"""
from __future__ import annotations

import numpy as np

from core.config import settings
from core.errors import APIError
from core.logging import get_logger

logger = get_logger(__name__)

_model = None   # lazy SentenceTransformer singleton (local path only)


def _load_model():
    """Load the local SentenceTransformer once. Raises RuntimeError if model not cached."""
    global _model
    if _model is not None:
        return _model
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(settings.EMBEDDING_MODEL_LOCAL)
        logger.info("Loaded local embedding model: %s", settings.EMBEDDING_MODEL_LOCAL)
        return _model
    except Exception as exc:
        raise RuntimeError(
            f"Local embedding model '{settings.EMBEDDING_MODEL_LOCAL}' not found in HF cache. "
            "Run scripts/download_models.sh before starting the stack."
        ) from exc


def _l2_normalise(vec: np.ndarray) -> np.ndarray:
    """L2-normalise so cosine similarity == dot product."""
    norm = float(np.linalg.norm(vec))
    return (vec / norm).astype(np.float32) if norm > 0 else vec.astype(np.float32)


def embed_text(text: str) -> np.ndarray:
    """
    Return a VECTOR_DIMENSIONS-length (768), L2-normalised float32 embedding.
    Uses the local model by default (EMBEDDING_MODEL_ACTIVE=local).
    Switches to gemini-embedding-001 API when EMBEDDING_MODEL_ACTIVE=api.
    """
    if settings.embedding_is_local():
        try:
            model = _load_model()
            vec = np.asarray(model.encode(text, normalize_embeddings=True), dtype=np.float32)
            return _l2_normalise(vec)
        except RuntimeError as exc:
            logger.error("Local embedding failed: %s", exc)
            raise APIError("embedding_unavailable", status_code=503)
        except Exception as exc:
            logger.error("Unexpected local embedding error: %s", exc)
            raise APIError("embedding_unavailable", status_code=503)
    else:
        # API path — gemini-embedding-001 returns >768 dims (MRL); truncate then renormalise
        try:
            import litellm
            resp = litellm.embedding(model=settings.EMBEDDING_MODEL_API, input=[text])
            vec = np.array(resp["data"][0]["embedding"], dtype=np.float32)
            vec = vec[:settings.VECTOR_DIMENSIONS]  # truncate MRL output to locked 768 dims
            return _l2_normalise(vec)
        except Exception as exc:
            logger.error("API embedding failed (%s): %s", settings.EMBEDDING_MODEL_API, exc)
            raise APIError("embedding_unavailable", status_code=503)


def embed_batch(texts: list[str]) -> list[np.ndarray]:
    """
    Embed a list of texts efficiently.
    Local path: uses SentenceTransformer batch encode (faster than looping embed_text).
    API path: calls embed_text per item (Gemini embedding API is single-item).
    """
    if settings.embedding_is_local():
        try:
            model = _load_model()
            vecs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
            return [_l2_normalise(np.asarray(v, dtype=np.float32)) for v in vecs]
        except RuntimeError as exc:
            logger.error("Local batch embedding failed: %s", exc)
            raise APIError("embedding_unavailable", status_code=503)
        except Exception as exc:
            logger.error("Unexpected local batch embedding error: %s", exc)
            raise APIError("embedding_unavailable", status_code=503)
    else:
        return [embed_text(t) for t in texts]


def is_stub() -> bool:
    """Always False — no stubs in live mode."""
    return False


def build_embedding_input(profile) -> str:
    """
    Single source of truth for the embedding input template — used at first ingest AND
    every re-embed. Accepts any object exposing expertise_areas, methodological_skills,
    and summary. Changing this template invalidates all stored embeddings (re-embed required).
    """
    return (
        f"EXPERTISE: {'; '.join(profile.expertise_areas)}; "
        f"SKILLS: {'; '.join(profile.methodological_skills)}; "
        f"SUMMARY: {profile.summary}"
    )