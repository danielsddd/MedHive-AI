"""
Embedding-service contract tests. Verify the Phase 0 guarantees that everything downstream
relies on: output is exactly 768-dim, L2-normalised (norm == 1.0), and deterministic for a
fixed input. These hold for both the real model and the offline stub, so the dimension
guard and matching math are safe regardless of environment.
"""
import numpy as np

from core.config import settings
from services import embedding


def test_dimension_is_768():
    vec = embedding.embed_text("medical researcher oncology")
    assert len(vec) == settings.VECTOR_DIMENSIONS == 768


def test_vector_is_l2_normalised():
    vec = embedding.embed_text("cardiology imaging")
    assert abs(float(np.linalg.norm(vec)) - 1.0) < 1e-5


def test_embedding_is_deterministic():
    a = embedding.embed_text("same input text")
    b = embedding.embed_text("same input text")
    assert np.allclose(a, b)


def test_build_embedding_input_template():
    class P:
        expertise_areas = ["oncology", "genomics"]
        methodological_skills = ["RNA-seq"]
        summary = "Cancer researcher."

    out = embedding.build_embedding_input(P())
    assert out.startswith("EXPERTISE: oncology; genomics; SKILLS: RNA-seq; SUMMARY:")
