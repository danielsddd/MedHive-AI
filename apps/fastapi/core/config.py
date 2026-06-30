"""
Central application settings — the SINGLE source of truth for every tunable value,
model string, rate cap, and secret. All model names live here as config strings and
are never hard-coded in business logic. Keys are REQUIRED — the app runs live only.
Daniel and Roei each keep their own keys in the shared .env (suffixed _DANIEL / _ROEI).
gemini_keys() / groq_keys() / cerebras_keys() return them in priority order so the
gateway can automatically rotate to the next student's key on a rate-limit error —
no manual .env editing needed when one key's quota runs out.
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
    EXTRACTION_MODEL: str = "gemini/gemini-2.5-flash"
    EXPLANATION_MODEL: str = "groq/openai/gpt-oss-120b"
    EXPLANATION_FALLBACK: str = "groq/openai/gpt-oss-20b"
    EMBEDDING_MODEL_LOCAL: str = "all-mpnet-base-v2"
    EMBEDDING_MODEL_API: str = "gemini-embedding-001"
    EMBEDDING_MODEL_ACTIVE: str = "local"               # local | api
    ACTIVE_EMBEDDING_COLUMN: str = "embedding"

    # ---- Infrastructure ----
    DATABASE_URL: str = "postgresql+asyncpg://app:change_me_local_only@postgres:5432/medcollab"
    REDIS_URL: str = "redis://redis:6379/0"

    # ---- Provider API keys — per-student, REQUIRED at least one per provider ----
    # Daniel's key is tried first; Roei's is the automatic rotation target on rate limit.
    GEMINI_API_KEY_DANIEL: str | None = None
    GEMINI_API_KEY_ROEI: str | None = None
    GROQ_API_KEY_DANIEL: str | None = None
    GROQ_API_KEY_ROEI: str | None = None
    CEREBRAS_API_KEY_DANIEL: str | None = None
    CEREBRAS_API_KEY_ROEI: str | None = None
    GITHUB_MODELS_TOKEN: str | None = None

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
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    def gemini_keys(self) -> list[str]:
        """Daniel's key first, then Roei's. Used by the gateway for automatic rotation."""
        return [k for k in (self.GEMINI_API_KEY_DANIEL, self.GEMINI_API_KEY_ROEI) if k]

    def groq_keys(self) -> list[str]:
        return [k for k in (self.GROQ_API_KEY_DANIEL, self.GROQ_API_KEY_ROEI) if k]

    def cerebras_keys(self) -> list[str]:
        return [k for k in (self.CEREBRAS_API_KEY_DANIEL, self.CEREBRAS_API_KEY_ROEI) if k]

    def llm_is_live(self) -> bool:
        return bool(self.gemini_keys() and self.groq_keys())

    def embedding_is_local(self) -> bool:
        return self.EMBEDDING_MODEL_ACTIVE == "local"

    def auth_is_live(self) -> bool:
        return True     # always live — Supabase keys are required fields


settings = Settings()

if not settings.gemini_keys():
    raise RuntimeError(
        "No Gemini key configured. Set GEMINI_API_KEY_DANIEL and/or GEMINI_API_KEY_ROEI in .env."
    )
if not settings.groq_keys():
    raise RuntimeError(
        "No Groq key configured. Set GROQ_API_KEY_DANIEL and/or GROQ_API_KEY_ROEI in .env."
    )