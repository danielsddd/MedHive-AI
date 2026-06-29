/**
 * TypeScript mirror of the LOCKED ResearcherProfile extraction contract defined in
 * apps/fastapi/schemas/researcher_profile.py. The backend is the source of truth; this file
 * gives the frontend typed access to the same shape (profile forms, review screens). MeSH tags
 * are intentionally absent — they are attached later by the verified tagger, never by the LLM.
 */
export interface Institution {
  name: string
  department?: string | null
  country?: string | null
}

export interface ResearcherProfile {
  full_name: string
  expertise_areas: string[] // 3-10 canonical research domain phrases
  methodological_skills: string[]
  keywords: string[] // free keywords; MeSH added by tagger, not here
  affiliation?: Institution | null
  summary: string // <=120-word structured professional summary
  education: string[]
  notable_publications: string[]
  confidence?: number | null // 0..1 LLM self-estimate; low => needs_review
}
