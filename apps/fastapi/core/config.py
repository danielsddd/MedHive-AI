"""
Central application settings — the SINGLE source of truth for every tunable value,
model string, rate cap, and secret. All model names live here as config strings and
are never hard-coded in business logic. Secrets are optional so the app boots with
zero keys (offline/stub mode); dropping a real key into .env flips a provider to live
with no code change. Loaded once at import as the module-level `settings` singleton.
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

    # ---- Run modes: auto | live | offline (dev) ----
    LLM_MODE: str = "auto"
    EMBEDDING_MODE: str = "auto"
    AUTH_MODE: str = "auto"

    # ---- Locked dimension ----
    VECTOR_DIMENSIONS: int = 768

    # ---- Model strings (config only) ----
    EXTRACTION_MODEL: str = "gemini/gemini-2.5-flash"
    EXTRACTION_FALLBACK: str = "groq/llama-3.3-70b-versatile"
    EXPLANATION_MODEL: str = "groq/llama-3.3-70b-versatile"
    EXPLANATION_FALLBACK: str = "groq/llama-3.1-8b-instant"
    EMBEDDING_MODEL_LOCAL: str = "all-mpnet-base-v2"
    EMBEDDING_MODEL_API: str = "gemini-embedding-001"
    EMBEDDING_MODEL_ACTIVE: str = "local"          # local | api
    ACTIVE_EMBEDDING_COLUMN: str = "embedding"

    # ---- Infrastructure ----
    DATABASE_URL: str = "postgresql+asyncpg://app:change_me_local_only@postgres:5432/medcollab"
    REDIS_URL: str = "redis://redis:6379/0"

    # ---- Provider keys (blank => stub) ----
    GEMINI_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None
    CEREBRAS_API_KEY: str | None = None
    GITHUB_MODELS_TOKEN: str | None = None

    # ---- Supabase Auth ----
    SUPABASE_URL: str | None = None
    SUPABASE_ANON_KEY: str | None = None
    SUPABASE_SERVICE_ROLE_KEY: str | None = None

    # ---- Rate caps ----
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
        # asyncpg wants a plain postgresql:// DSN (no SQLAlchemy +asyncpg suffix).
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    def has_any_llm_key(self) -> bool:
        return any([self.GEMINI_API_KEY, self.GROQ_API_KEY,
                    self.CEREBRAS_API_KEY, self.GITHUB_MODELS_TOKEN])

    def llm_is_live(self) -> bool:
        if self.LLM_MODE == "live":
            return True
        if self.LLM_MODE in ("offline", "dev"):
            return False
        return self.has_any_llm_key()           # auto

    def embedding_is_local(self) -> bool:
        return self.EMBEDDING_MODEL_ACTIVE == "local"

    def auth_is_live(self) -> bool:
        if self.AUTH_MODE == "live":
            return True
        if self.AUTH_MODE in ("offline", "dev"):
            return False
        return bool(self.SUPABASE_URL and self.SUPABASE_SERVICE_ROLE_KEY)   # auto


settings = Settings()
