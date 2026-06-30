"""
LLM-based structured extraction (step 1.3). Wraps the EXTRACTION_MODEL (Gemini 2.5 Flash)
with Instructor so the response is forced into the LOCKED ResearcherProfile schema —
Instructor handles JSON-shape retries on malformed output automatically. Reuses the same
Daniel/Roei key-rotation list as llm_gateway.py: if the first key hits a rate limit,
the extraction call rotates to the next key before giving up, exactly mirroring the
resilience behaviour of complete()/explain(). If confidence comes back below the
threshold, the caller (the ARQ task in 1.6) marks the profile status='needs_review'
instead of treating it as a hard failure — extraction must never silently block ingest.
"""
from __future__ import annotations

from core.errors import ERRORS, APIError
from core.logging import get_logger
from schemas.researcher_profile import ResearcherProfile

from core.config import settings

logger = get_logger(__name__)

# Below this confidence, the caller marks the profile needs_review rather than active.
LOW_CONFIDENCE_THRESHOLD = 0.55

_SYSTEM_PROMPT = (
    "You are extracting a structured researcher profile from a CV or publication list. "
    "Extract ONLY information explicitly present in the text — never invent affiliations, "
    "publications, or skills. expertise_areas must be 3-10 canonical research domain "
    "phrases (e.g. 'oncology', 'single-cell genomics'), not full sentences. "
    "methodological_skills are concrete techniques/methods actually used "
    "(e.g. 'RNA-seq', 'Cox regression', 'MRI acquisition'). summary is a neutral, "
    "third-person professional summary under 120 words. notable_publications are titles "
    "only, taken verbatim from the text — do not summarise or paraphrase them. Set "
    "confidence between 0 and 1 reflecting how complete and unambiguous the source text "
    "was for this extraction; use a LOW confidence if the CV is sparse, garbled, or "
    "missing obvious sections."
)


async def extract_profile(cv_text: str) -> ResearcherProfile:
    """
    Runs structured extraction against EXTRACTION_MODEL via Instructor, rotating across
    all configured Gemini keys on rate limit (same pattern as llm_gateway._try_keys).
    Raises APIError('extraction_failed') if every key fails or output never validates.
    """
    keys = settings.gemini_keys()
    if not keys:
        raise APIError(
            "provider_unavailable", "No Gemini API key configured.", status_code=503
        )

    import instructor
    import litellm

    last_exc: Exception | None = None
    for i, key in enumerate(keys):
        try:
            client = instructor.from_litellm(litellm.acompletion)
            profile = await client.chat.completions.create(
                model=settings.EXTRACTION_MODEL,
                api_key=key,
                max_retries=2,  # Instructor's own retry-on-validation-failure budget
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": cv_text},
                ],
                response_model=ResearcherProfile,
            )
            return profile
        except litellm.exceptions.RateLimitError as exc:
            last_exc = exc
            who = "Daniel" if i == 0 else "Roei"
            logger.warning(
                "Extraction rate limit (key #%d/%s) -> rotating to next key", i + 1, who
            )
            continue
        except Exception as exc:
            last_exc = exc
            logger.error("Extraction failed on key #%d: %s", i + 1, exc)
            # A validation/parsing failure is not a rate limit — no point rotating keys
            # for it, but we still try the next key once in case it was a transient
            # provider-side issue rather than a genuine schema mismatch.
            continue

    logger.error("All keys exhausted during extraction: %s", last_exc)
    raise APIError(
        "extraction_failed", ERRORS["extraction_failed"], status_code=502
    ) from last_exc


def needs_review(profile: ResearcherProfile) -> bool:
    """True if the extraction confidence is low enough to require human review."""
    return profile.confidence is not None and profile.confidence < LOW_CONFIDENCE_THRESHOLD
