"""
The ARQ ingest task (step 1.6) — the actual Profile Builder pipeline: parse the uploaded
CV, extract a structured profile via the LLM, embed it, and write profile + embedding to
Postgres in one transaction. Designed to never leave a half-written row: job_status is
updated at each stage (queued -> running -> done|failed) so the frontend can poll
progress, and any failure writes a typed error onto the job row instead of crashing the
worker. Retries are handled by ARQ's own retry mechanism at the task-enqueue level
(see routers/profiles.py); this function itself is the single attempt body.
"""
from __future__ import annotations

import uuid

from core.errors import APIError
from core.logging import get_logger
from db.session import execute, fetchrow

from services import audit
from services.embedding import build_embedding_input, embed_text
from services.extractor import extract_profile, needs_review
from services.parser import parse_cv

logger = get_logger(__name__)


async def run_ingest(
    ctx: dict, job_id: str, user_id: str, file_bytes: bytes, content_type: str
) -> None:
    """
    ARQ task body. ctx is ARQ's per-job context dict (unused here beyond the signature
    ARQ requires). Always updates job_status before returning, success or failure —
    the frontend polls GET /jobs/{id} and must never see a job stuck at 'running'.
    """
    await _set_job_status(job_id, "running")

    try:
        cv_text = parse_cv(file_bytes, content_type)
        profile = await extract_profile(cv_text)
        status = "needs_review" if needs_review(profile) else "active"

        embedding_input = build_embedding_input(profile)
        vector = embed_text(embedding_input)

        profile_id = await _store_profile(user_id, profile, vector, status)

        await _set_job_status(job_id, "done", profile_id=profile_id)
        await audit.log(
            actor_id=uuid.UUID(user_id),
            action="profile_ingested",
            entity_type="profile",
            entity_id=uuid.UUID(profile_id),
            payload={"status": status, "confidence": profile.confidence},
        )
    except APIError as exc:
        logger.warning("Ingest job %s failed with %s: %s", job_id, exc.code, exc.detail)
        await _set_job_status(
            job_id, "failed", error_code=exc.code, error_message=exc.detail.get("message")
        )
    except Exception as exc:
        logger.error("Ingest job %s failed unexpectedly: %s", job_id, exc, exc_info=True)
        await _set_job_status(
            job_id,
            "failed",
            error_code="internal_error",
            error_message="Unexpected error during ingest.",
        )


async def _store_profile(user_id: str, profile, vector, status: str) -> str:
    """
    Writes the profile row (including the 768-dim embedding) in a single INSERT, with
    an UPSERT on the existing unique(user_id) constraint so re-ingesting replaces the
    prior profile rather than erroring or duplicating. Returns the profile id as a string.
    """
    affiliation_name = profile.affiliation.name if profile.affiliation else None
    vector_literal = "[" + ",".join(str(float(x)) for x in vector) + "]"

    row = await fetchrow(
        """
        INSERT INTO profiles (
            user_id, full_name, expertise_areas, methodological_skills, keywords,
            summary, education, notable_publications, confidence, status,
            embedding, embedding_model_ver, source
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::vector, $12, 'cv')
        ON CONFLICT (user_id) DO UPDATE SET
            full_name = EXCLUDED.full_name,
            expertise_areas = EXCLUDED.expertise_areas,
            methodological_skills = EXCLUDED.methodological_skills,
            keywords = EXCLUDED.keywords,
            summary = EXCLUDED.summary,
            education = EXCLUDED.education,
            notable_publications = EXCLUDED.notable_publications,
            confidence = EXCLUDED.confidence,
            status = EXCLUDED.status,
            embedding = EXCLUDED.embedding,
            embedding_model_ver = EXCLUDED.embedding_model_ver,
            updated_at = now()
        RETURNING id
        """,
        uuid.UUID(user_id),
        profile.full_name,
        profile.expertise_areas,
        profile.methodological_skills,
        profile.keywords,
        profile.summary,
        profile.education,
        profile.notable_publications,
        profile.confidence,
        status,
        vector_literal,
        "all-mpnet-base-v2",
    )
    # affiliation_name is intentionally not written here yet — affiliation -> institutions
    # FK resolution (find-or-create institution row) is deferred to a follow-up pass so
    # the core ingest path stays simple; affiliation is preserved in the LLM response and
    # not lost, just not yet linked relationally.
    _ = affiliation_name
    return str(row["id"])


async def _set_job_status(
    job_id: str,
    status: str,
    profile_id: str | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
) -> None:
    await execute(
        """
        UPDATE job_status
        SET status = $2, profile_id = $3, error_code = $4, error_message = $5, updated_at = now()
        WHERE id = $1
        """,
        uuid.UUID(job_id),
        status,
        uuid.UUID(profile_id) if profile_id else None,
        error_code,
        error_message,
    )
