"""
LOCKED LLM-extraction contract. These exact fields define the structured profile the
extractor must return and are mirrored 1:1 in packages/types/researcher-profile.ts.
Changing this shape requires a DB migration and re-running EXP-iii. MeSH tags are NOT
present here on purpose — they are added later by the verified NLM tagger, never invented
by the LLM. Used by Instructor to enforce the output schema during extraction.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class Institution(BaseModel):
    name: str
    department: str | None = None
    country: str | None = None


class ResearcherProfile(BaseModel):
    full_name: str
    expertise_areas: list[str] = Field(
        ..., min_length=3, max_length=10,
        description="3-10 canonical research domain phrases",
    )
    methodological_skills: list[str] = Field(
        ..., description="e.g. 'single-cell RNA-seq', 'Cox regression', 'MRI acquisition'",
    )
    keywords: list[str] = Field(
        ..., description="Free keywords; MeSH tags are added by the tagger, NOT here",
    )
    affiliation: Institution | None = None
    summary: str = Field(..., description="<=120-word structured professional summary")
    education: list[str] = Field(default_factory=list, description="'degree, institution, year'")
    notable_publications: list[str] = Field(
        default_factory=list, description="Titles only; verified externally, never trust the CV",
    )
    confidence: float | None = Field(
        default=None, ge=0.0, le=1.0,
        description="LLM self-estimate; below threshold -> status=needs_review",
    )
