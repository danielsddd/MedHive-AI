"""
Stable, user-safe error contract for the whole API. Every failure surfaces as
{"code": "STABLE_CODE", "message": "human-readable"} and never leaks a stack trace.
STABLE codes are frozen once shipped — the frontend's errorToMessage() maps them to
toast copy. Raise APIError anywhere; the FastAPI exception handlers (main.py) render it.
"""
from __future__ import annotations

from fastapi import HTTPException


class APIError(HTTPException):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(status_code=status_code, detail={"code": code, "message": message})
        self.code = code


# Frozen catalogue of stable codes. Add new ones; never rename existing ones.
ERRORS: dict[str, str] = {
    "cv_unreadable": "We couldn't extract text from this file. Try pasting your CV text.",
    "unsupported_file_type": "Please upload a PDF or DOCX file.",
    "file_too_large": "File exceeds the maximum allowed size.",
    "extraction_failed": "Profile extraction failed. Please try again.",
    "embedding_unavailable": "Matching is temporarily unavailable. Try again in a moment.",
    "profile_not_found": "Profile not found.",
    "not_authorized": "You don't have permission to do this.",
    "rate_limit_exceeded": "Too many requests. Please wait before trying again.",
    "job_not_found": "Job not found.",
    "jwt_invalid": "Your session is invalid or has expired. Please sign in again.",
    "internal_error": "Something went wrong. Please try again.",
}


def error_body(code: str, message: str | None = None) -> dict[str, str]:
    return {"code": code, "message": message or ERRORS.get(code, "Unexpected error.")}
