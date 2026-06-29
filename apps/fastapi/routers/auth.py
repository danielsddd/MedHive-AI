"""
Auth-related read endpoints. GET /me returns the current user and role (401 with stable
code jwt_invalid if the token is missing/invalid). All business logic lives in FastAPI —
Next.js only forwards the Supabase JWT here. Protected routes elsewhere reuse the same
get_current_user dependency.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from schemas.common import MeResponse
from services.auth import CurrentUser, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=MeResponse)
async def me(user: CurrentUser = Depends(get_current_user)) -> MeResponse:
    return MeResponse(user_id=str(user.id), email=user.email, role=user.role)
