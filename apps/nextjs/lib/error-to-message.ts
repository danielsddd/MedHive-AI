/**
 * Single source of truth that maps backend STABLE error codes to friendly toast copy.
 * Mirrors the codes in apps/fastapi/core/errors.py. Unknown codes fall back to a generic
 * message so a raw stack trace or code is never shown to the user.
 */
export const errorToMessage = (code: string): string =>
  ({
    cv_unreadable: "We couldn't read this file. Try pasting your CV text below.",
    unsupported_file_type: 'Please upload a PDF or DOCX file.',
    file_too_large: 'That file is too large.',
    extraction_failed: 'Profile extraction failed. Please try again.',
    embedding_unavailable: 'Matching is temporarily unavailable.',
    profile_not_found: 'Profile not found.',
    not_authorized: "You don't have permission to do this.",
    rate_limit_exceeded: "You're doing that too fast. Please wait a moment.",
    job_not_found: 'Job not found.',
    jwt_invalid: 'Your session expired. Please sign in again.',
  })[code] ?? 'Something went wrong. Please try again.'
