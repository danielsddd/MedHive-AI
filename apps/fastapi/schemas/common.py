"""
Small shared response schemas used across routers: the stable error envelope and the
/healthz payload. Keeping these typed gives FastAPI's OpenAPI docs an accurate contract
and guarantees every error response matches the {"code","message"} shape the frontend
maps to toasts.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

Status = Literal["up", "down"]


class ErrorResponse(BaseModel):
    code: str
    message: str


class MeResponse(BaseModel):
    user_id: str
    email: str | None = None
    role: str


class HealthResponse(BaseModel):
    db: Status
    redis: Status
    embedding_service: Status
    gateway: Status
