"""
Shared cross-language constants (Python side, re-exported for any non-FastAPI tooling).
These MUST stay numerically identical to packages/types/constants.ts and
apps/fastapi/core/constants.py. Keeping a copy here lets scripts/ and notebooks import the
canonical values without importing the whole FastAPI app. VECTOR_DIMENSIONS is locked at 768.
"""

VECTOR_DIMENSIONS: int = 768

EMBEDDING_COLUMNS: tuple[str, ...] = (
    "embedding",
    "embedding_mpnet",
    "embedding_gemini",
    "embedding_biolord",
)

RBAC_ROLES: tuple[str, ...] = ("researcher", "reviewer", "admin", "institutional_admin")
DEFAULT_ROLE: str = "researcher"
