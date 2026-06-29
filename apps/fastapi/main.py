"""
FastAPI application entrypoint. On startup it runs the LOCKED dimension guard — the app
refuses to accept any request unless the live embedding model emits exactly
VECTOR_DIMENSIONS (768) — then initialises the DB pool. It installs global exception
handlers so every error returns the stable {"code","message"} shape with no stack trace,
wires CORS from config, and mounts the auth + health routers. Business logic lives here,
never in Next.js (one backend surface).
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import settings
from core.errors import APIError, error_body
from core.logging import configure_logging, get_logger
from db.session import close_pool, init_pool
from routers import auth, health
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
    yield
    await close_pool()


app = FastAPI(title="TAU 3346 — Medical Research Platform", version="0.0.0", lifespan=lifespan)

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


@app.exception_handler(Exception)
async def handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled error: %s", exc, exc_info=True)
    return JSONResponse(status_code=500, content=error_body("internal_error"))


app.include_router(health.router)
app.include_router(auth.router)
