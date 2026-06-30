"""
FastAPI application entrypoint. On startup it runs the LOCKED dimension guard — the app
refuses to accept any request unless the live embedding model emits exactly
VECTOR_DIMENSIONS (768) — then initialises the DB pool and an ARQ Redis pool (used to
enqueue background jobs, e.g. profile ingestion). It installs global exception handlers
so every error returns the stable {"code","message"} shape with no stack trace (including
slowapi rate-limit errors, mapped to the rate_limit_exceeded code), wires CORS from
config, and mounts the auth + health + profiles + jobs routers. Business logic lives
here, never in Next.js (one backend surface).
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from arq import create_pool
from arq.connections import RedisSettings
from core.errors import APIError, error_body
from core.logging import configure_logging, get_logger
from db.session import close_pool, init_pool
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from core.config import settings
from routers import auth, health, profiles
from routers.profiles import limiter
from services.embedding import embed_text

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    # LOCKED dimension guard — must run before serving any request.
    test_vec = embed_text("startup dimension check")
    assert len(test_vec) == settings.VECTOR_DIMENSIONS, (
        f"FATAL: embedding dimension mismatch. Got {len(test_vec)}, "
        f"expected {settings.VECTOR_DIMENSIONS}. Check EMBEDDING_MODEL_ACTIVE="
        f"'{settings.EMBEDDING_MODEL_ACTIVE}' and the HF model cache."
    )
    logger.info("Dimension guard passed (%d).", settings.VECTOR_DIMENSIONS)
    try:
        await init_pool()
    except Exception as exc:  # DB may be absent in pure unit runs; health reports down
        logger.warning("DB pool not initialised at startup: %s", exc)
    try:
        app.state.arq_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    except Exception as exc:  # Redis may be absent in pure unit runs; ingest will 503
        logger.warning("ARQ pool not initialised at startup: %s", exc)
        app.state.arq_pool = None
    yield
    await close_pool()
    if getattr(app.state, "arq_pool", None) is not None:
        await app.state.arq_pool.close()


app = FastAPI(title="TAU 3346 — Medical Research Platform", version="0.0.0", lifespan=lifespan)

app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(APIError)
async def handle_api_error(_: Request, exc: APIError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.detail)


@app.exception_handler(RateLimitExceeded)
async def handle_rate_limit(_: Request, _exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(status_code=429, content=error_body("rate_limit_exceeded"))


@app.exception_handler(Exception)
async def handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled error: %s", exc, exc_info=True)
    return JSONResponse(status_code=500, content=error_body("internal_error"))


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(profiles.router)
app.include_router(profiles.jobs_router)