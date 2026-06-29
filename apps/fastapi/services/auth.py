"""
Authentication boundary. In live mode it validates the Supabase-issued JWT on every
protected route and returns the current user; in dev/offline mode (no Supabase keys) it
accepts any bearer token and returns a stable dev user, so the frontend and protected
routes can be built before auth is wired. Roles are read as DATA (user_roles table),
never as if-statements. The service-role key stays here in the backend and is never logged.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.config import settings
from core.constants import DEFAULT_ROLE
from core.errors import APIError
from core.logging import get_logger

logger = get_logger(__name__)
security = HTTPBearer(auto_error=False)

# Fixed identity used only in dev/offline mode so flows are reproducible.
_DEV_USER_ID = uuid.UUID("00000000-0000-0000-0000-0000000000d0")


@dataclass(frozen=True)
class CurrentUser:
    id: uuid.UUID
    email: str | None
    role: str


def _supabase_client():
    from supabase import create_client  # lazy import; not needed in dev mode

    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(security),
) -> CurrentUser:
    """FastAPI dependency: resolves the caller or raises 401 with a stable error code."""
    if creds is None or not creds.credentials:
        raise APIError("jwt_invalid", "Missing bearer token.", status_code=401)

    if not settings.auth_is_live():
        # Dev/offline: trust the presented token, return the stable dev user.
        return CurrentUser(id=_DEV_USER_ID, email="dev@local", role=DEFAULT_ROLE)

    try:
        resp = _supabase_client().auth.get_user(creds.credentials)
        if not resp or not resp.user:
            raise APIError("jwt_invalid", "Invalid token.", status_code=401)
        user = resp.user
    except APIError:
        raise
    except Exception as exc:
        logger.warning("JWT validation failed: %s", type(exc).__name__)
        raise APIError("jwt_invalid", "Invalid token.", status_code=401) from exc

    role = await _lookup_role(uuid.UUID(user.id))
    return CurrentUser(id=uuid.UUID(user.id), email=getattr(user, "email", None), role=role)


async def _lookup_role(user_id: uuid.UUID) -> str:
    """Read the role from user_roles; default to researcher if no row yet."""
    from db.session import fetchval

    row = await fetchval("SELECT role FROM user_roles WHERE user_id = $1", user_id)
    return row or DEFAULT_ROLE
