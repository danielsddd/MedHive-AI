"""
Immutable, code-level constants that must agree with the database migrations and the
shared packages/types values. VECTOR_DIMENSIONS is duplicated here intentionally as a
belt-and-braces guard: the startup assert compares the live model against it. Changing
768 here without re-creating every embedding column and re-embedding every row is a
hard-rule violation.
"""

VECTOR_DIMENSIONS: int = 768

# Embedding column names that physically exist in the `profiles` table (migration m2).
EMBEDDING_COLUMNS: tuple[str, ...] = (
    "embedding",          # active production column
    "embedding_mpnet",    # EXP-i baseline
    "embedding_gemini",   # EXP-i API comparison
    "embedding_biolord",  # EXP-i+ biomedical
)

RBAC_ROLES: tuple[str, ...] = ("researcher", "reviewer", "admin", "institutional_admin")
DEFAULT_ROLE: str = "researcher"
