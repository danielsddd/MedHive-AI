"""
Central application settings — the SINGLE source of truth for every tunable value,
model string, rate cap, and secret. All model names live here as config strings and
are never hard-coded in business logic. Keys are REQUIRED — the app runs live only.
Both students (Daniel + Roei) keep their own keys in the shared .env; swapping the
active key is a one-line .env edit, never a code change.
Loaded once at import as the module-level `settings` singleton.
"""
from __future__ import annotations

from functools import cached_property

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- Run modes (always live — keys are required) ----
    LLM_MODE: str = "live"
    EMBEDDING_MODE: str = "live"
    AUTH_MODE: str = "live"

    # ---- Locked dimension (never change) ----
    VECTOR_DIMENSIONS: int = 768

    # ---- Model strings (config only — never hard-coded in logic) ----
    # Gemini 2.5 Flash: best free model for long CV extraction (1M context window)
    EXTRACTION_MODEL: str = "gemini/gemini-2.5-flash"
    # gpt-oss-120b: Groq's recommended replacement for llama-3.3-70b (deprecated Jun 17 2026)
    EXPLANATION_MODEL: str = "groq/openai/gpt-oss-120b"
    # gpt-oss-20b: Groq's recommended replacement for llama-3.1-8b-instant (deprecated Jun 17 2026)
    EXPLANATION_FALLBACK: str = "groq/openai/gpt-oss-20b"
    # Embedding models
    EMBEDDING_MODEL_LOCAL: str = "all-mpnet-base-v2"    # self-hosted, 768-dim, locked
    EMBEDDING_MODEL_API: str = "gemini-embedding-001"   # API path, truncate+renorm to 768
    EMBEDDING_MODEL_ACTIVE: str = "local"               # local | api
    ACTIVE_EMBEDDING_COLUMN: str = "embedding"

    # ---- Infrastructure ----
    DATABASE_URL: str = "postgresql+asyncpg://app:change_me_local_only@postgres:5432/medcollab"
    REDIS_URL: str = "redis://redis:6379/0"

    # ---- Provider API keys (REQUIRED — no stubs, no fallback to a different provider) ----
    # Swap between _DANIEL and _ROEI values in .env when hitting rate limits
    GEMINI_API_KEY: str                 # extraction LLM + API embeddings
    GROQ_API_KEY: str                   # explanation LLM
    CEREBRAS_API_KEY: str | None = None # optional — available if needed
    GITHUB_MODELS_TOKEN: str | None = None  # optional — available if needed

    # ---- Supabase Auth (JWT issuer only — app DB is local pgvector) ----
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str      # BACKEND-ONLY — never log or expose to frontend

    # ---- Rate caps (50% of each provider's free-tier limit) ----
    INGEST_PER_HOUR: int = 3
    EXPLAIN_PER_MIN: int = 10
    MATCH_PER_MIN: int = 30

    # ---- Parsing guards ----
    CV_MIN_CHARS: int = 200
    CV_MAX_TOKENS: int = 12_000
    MAX_FILE_MB: int = 20

    # ---- Misc ----
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @cached_property
    def asyncpg_dsn(self) -> str:
        # asyncpg wants a plain postgresql:// DSN (no SQLAlchemy +asyncpg suffix)
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    def llm_is_live(self) -> bool:
        return True     # always live — keys are required fields

    def embedding_is_local(self) -> bool:
        return self.EMBEDDING_MODEL_ACTIVE == "local"

    def auth_is_live(self) -> bool:
        return True     # always live — keys are required fields


settings = Settings()