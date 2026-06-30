"""
Request/response schemas for the Profile Builder endpoints (POST /profiles/ingest,
GET /jobs/{id}, GET /profiles/me). Separate from the LOCKED ResearcherProfile extraction
contract in researcher_profile.py — these describe the API surface and job lifecycle,
not the extraction shape itself.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel
from schemas.researcher_profile import Institution

JobStatus = Literal["queued", "running", "done", "failed"]
ProfileStatus = Literal["active", "needs_review", "failed"]


class IngestResponse(BaseModel):
    """Returned immediately by POST /profiles/ingest — extraction runs async."""
    job_id: str
    status: JobStatus = "queued"


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    profile_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class ProfileResponse(BaseModel):
    """Full profile as returned to the owning user (GET /profiles/me)."""
    id: str
    user_id: str
    full_name: str | None = None
    expertise_areas: list[str] = []
    methodological_skills: list[str] = []
    keywords: list[str] = []
    affiliation: Institution | None = None
    summary: str | None = None
    education: list[str] = []
    notable_publications: list[str] = []
    confidence: float | None = None
    status: ProfileStatus
    created_at: datetime
    updated_at: datetime


class ProfileUpdateRequest(BaseModel):
    """PUT /profiles/{id} — partial update; any text-field change triggers a re-embed."""
    full_name: str | None = None
    expertise_areas: list[str] | None = None
    methodological_skills: list[str] | None = None
    keywords: list[str] | None = None
    summary: str | None = None
    education: list[str] | None = None
    notable_publications: list[str] | None = None
