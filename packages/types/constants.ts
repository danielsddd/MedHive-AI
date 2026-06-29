/**
 * Shared cross-language constants (TypeScript side). These MUST stay numerically identical
 * to packages/types/constants.py and apps/fastapi/core/constants.py. VECTOR_DIMENSIONS is the
 * locked embedding width; the embedding columns and RBAC roles mirror the database migrations.
 * Frontend code imports from here so a single edit propagates everywhere.
 */
export const VECTOR_DIMENSIONS = 768 as const

export const EMBEDDING_COLUMNS = [
  'embedding', // active production column
  'embedding_mpnet', // EXP-i baseline
  'embedding_gemini', // EXP-i API comparison
  'embedding_biolord', // EXP-i+ biomedical
] as const

export const RBAC_ROLES = ['researcher', 'reviewer', 'admin', 'institutional_admin'] as const
export const DEFAULT_ROLE = 'researcher' as const

export type RbacRole = (typeof RBAC_ROLES)[number]
