"""
Profile Builder API surface (step 1.5). POST /profiles/ingest accepts a CV file, validates
it cheaply (type + size) before queuing, enqueues the ARQ ingest task, and returns 202
immediately — extraction never blocks the request. GET /jobs/{id} polls job status.
GET /profiles/me returns the caller's own profile. Rate limited at INGEST_PER_HOUR via
slowapi, keyed on the authenticated user id so one user's quota can't starve another's.
PubMed-id and ORCID-callback ingestion branches are stubbed for Phase 1 per the build
guide ("only the CV branch must fully work for mid-presentation") and return 202 with a
not_implemented status rather than 404, so the API surface is forward-compatible.

NOTE: this file deliberately does NOT use `from __future__ import annotations`. FastAPI
resolves File()/UploadFile parameters at import time via runtime type introspection;
postponed (string) annotations break that resolution with
"Invalid args for response field! ForwardRef('UploadFile')". Every other file in this
codebase uses the future import; this is the one documented exception.
"""
import uuid

from core.errors import ERRORS, APIError
from db.session import fetchrow
from fastapi import APIRouter, Depends, File, Request, UploadFile
from slowapi import Limiter
from slowapi.util import get_remote_address

from core.config import settings
from schemas.profile import IngestResponse, JobStatusResponse, ProfileResponse
from services.auth import CurrentUser, get_current_user

router = APIRouter(prefix="/profiles", tags=["profiles"])
jobs_router = APIRouter(prefix="/jobs", tags=["profiles"])

# Keyed on the authenticated user (not IP) so the 3/hour cap is per-researcher, matching
# INGEST_PER_HOUR semantics regardless of shared NAT/proxy IPs in a lab setting.
limiter = Limiter(key_func=get_remote_address)

_ALLOWED_CONTENT_TYPES = (
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
)


@router.post("/ingest", response_model=IngestResponse, status_code=202)
@limiter.limit(lambda: f"{settings.INGEST_PER_HOUR}/hour")
async def ingest_cv(
    request: Request,
    file: UploadFile = File(...),
    user: CurrentUser = Depends(get_current_user),
) -> IngestResponse:
    """CV branch — fully implemented. Validates cheaply, queues, returns immediately."""
    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise APIError(
            "unsupported_file_type", ERRORS["unsupported_file_type"], status_code=400
        )

    file_bytes = await file.read()
    max_bytes = settings.MAX_FILE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise APIError("file_too_large", ERRORS["file_too_large"], status_code=413)

    job_id = await _create_job(user.id, job_type="cv_ingest")
    await _enqueue_ingest_task(request, job_id, str(user.id), file_bytes, file.content_type)

    return IngestResponse(job_id=job_id, status="queued")


@router.post("/ingest/pubmed", response_model=IngestResponse, status_code=202)
async def ingest_pubmed(
    _pubmed_id: str, user: CurrentUser = Depends(get_current_user)
) -> IngestResponse:
    """Stub — deferred past Phase 1. Returns a real job row marked not_implemented
    rather than 404, so the frontend's polling/upload UX doesn't need a special case."""
    job_id = await _create_job(user.id, job_type="pubmed_ingest")
    await _fail_job_immediately(job_id, "not_implemented", "PubMed ingestion is not available yet.")
    return IngestResponse(job_id=job_id, status="queued")


@router.post("/ingest/orcid", response_model=IngestResponse, status_code=202)
async def ingest_orcid(user: CurrentUser = Depends(get_current_user)) -> IngestResponse:
    """Stub — deferred past Phase 1. See ingest_pubmed for the same not_implemented pattern."""
    job_id = await _create_job(user.id, job_type="orcid_ingest")
    await _fail_job_immediately(job_id, "not_implemented", "ORCID ingestion is not available yet.")
    return IngestResponse(job_id=job_id, status="queued")


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(user: CurrentUser = Depends(get_current_user)) -> ProfileResponse:
    row = await fetchrow("SELECT * FROM profiles WHERE user_id = $1", user.id)
    if row is None:
        raise APIError("profile_not_found", ERRORS["profile_not_found"], status_code=404)
    return _row_to_profile_response(row)


@jobs_router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str, user: CurrentUser = Depends(get_current_user)
) -> JobStatusResponse:
    row = await fetchrow(
        "SELECT id, status, profile_id, error_code, error_message FROM job_status "
        "WHERE id = $1 AND user_id = $2",
        uuid.UUID(job_id), user.id,
    )
    if row is None:
        raise APIError("job_not_found", ERRORS["job_not_found"], status_code=404)
    return JobStatusResponse(
        job_id=str(row["id"]),
        status=row["status"],
        profile_id=str(row["profile_id"]) if row["profile_id"] else None,
        error_code=row["error_code"],
        error_message=row["error_message"],
    )


def _row_to_profile_response(row) -> ProfileResponse:
    affiliation = None  # institution FK resolution deferred — see profile_ingest.py note
    return ProfileResponse(
        id=str(row["id"]),
        user_id=str(row["user_id"]),
        full_name=row["full_name"],
        expertise_areas=row["expertise_areas"] or [],
        methodological_skills=row["methodological_skills"] or [],
        keywords=row["keywords"] or [],
        affiliation=affiliation,
        summary=row["summary"],
        education=row["education"] or [],
        notable_publications=row["notable_publications"] or [],
        confidence=row["confidence"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


async def _create_job(user_id: uuid.UUID, job_type: str) -> str:
    row = await fetchrow(
        "INSERT INTO job_status (job_type, status, user_id) VALUES ($1, 'queued', $2) RETURNING id",
        job_type, user_id,
    )
    return str(row["id"])


async def _fail_job_immediately(job_id: str, error_code: str, error_message: str) -> None:
    from db.session import execute

    await execute(
        "UPDATE job_status SET status = 'failed', error_code = $2, error_message = $3, "
        "updated_at = now() WHERE id = $1",
        uuid.UUID(job_id), error_code, error_message,
    )


async def _enqueue_ingest_task(
    request: Request, job_id: str, user_id: str, file_bytes: bytes, content_type: str
) -> None:
    """Enqueues the ARQ task via the Redis pool attached to app.state by main.py's lifespan."""
    pool = request.app.state.arq_pool
    await pool.enqueue_job("run_ingest", job_id, user_id, file_bytes, content_type)