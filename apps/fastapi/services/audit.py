"""
Append-only audit logging. Every FastAPI endpoint that mutates data calls log() so each
write leaves an immutable trail (audit_logs is INSERT-only for the app role at the DB
level — migration m5). Payloads carry a diff or minimal context only — never raw PII or
secrets. Failures to log are surfaced in server logs but must not crash the request path.
"""
from __future__ import annotations

import json
import uuid

from core.logging import get_logger
from db.session import execute

logger = get_logger(__name__)


async def log(
    actor_id: uuid.UUID | None,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None,
    payload: dict | None = None,
) -> None:
    try:
        await execute(
            "INSERT INTO audit_logs (actor_id, action, entity_type, entity_id, payload) "
            "VALUES ($1, $2, $3, $4, $5::jsonb)",
            actor_id, action, entity_type, entity_id, json.dumps(payload or {}),
        )
    except Exception as exc:
        logger.error("audit.log failed for action=%s: %s", action, exc)
