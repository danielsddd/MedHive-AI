"""
Operational health endpoint. GET /healthz reports up|down for each dependency (db, redis,
embedding service, LLM gateway) so the healthcheck script and staging keep-alive cron can
detect a silently failing service. Every check is wrapped so the route itself never throws;
a failing dependency reports "down" rather than 500.
"""
from __future__ import annotations

from fastapi import APIRouter

from db import redis_client, session
from schemas.common import HealthResponse
from services import embedding, llm_gateway

router = APIRouter(tags=["ops"])


@router.get("/healthz", response_model=HealthResponse)
async def healthz() -> HealthResponse:
    db_ok = await session.ping()
    redis_ok = await redis_client.ping()

    try:
        vec = embedding.embed_text("healthz")
        embed_ok = len(vec) == 768
    except Exception:
        embed_ok = False

    gateway_ok = llm_gateway.gateway_status() in ("live", "offline")

    return HealthResponse(
        db="up" if db_ok else "down",
        redis="up" if redis_ok else "down",
        embedding_service="up" if embed_ok else "down",
        gateway="up" if gateway_ok else "down",
    )
