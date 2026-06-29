# Match Annotation Rubric

Used to score collaboration matches during evaluation (EXP-iii and ongoing quality checks).
Two annotators score independently; disagreements of ≥2 points are adjudicated. Track
inter-annotator agreement (Cohen's κ) across each batch.

## Relevance scale (per candidate pairing)
Rate how suitable the suggested collaborator is for the query researcher.

| Score | Label | Meaning |
| --- | --- | --- |
| 4 | Excellent | Clear, specific complementarity; a collaboration is easy to imagine and well-justified. |
| 3 | Good | Plausible overlap or complementarity; some adaptation needed but worth a conversation. |
| 2 | Marginal | Tangential relevance; shared field but unclear why these two specifically. |
| 1 | Poor | Little real overlap; likely surfaced by shallow keyword similarity. |
| 0 | Irrelevant | Wrong domain, duplicate of self, or nonsensical pairing. |

## Dimensions to consider
- **Topical overlap** — do their research areas genuinely intersect?
- **Complementarity** — do methods/skills fill each other's gaps (not just duplicate)?
- **Feasibility signals** — institution, seniority, and stated interests don't obviously block it.
- **Explanation quality** — does the generated rationale cite real, specific common ground rather
  than generic filler? Flag hallucinated or unsupported claims separately.

## Required flags (independent of the 0–4 score)
- `hallucinated_claim` — the explanation asserts something not supported by either profile.
- `self_or_duplicate` — candidate is the query user or a duplicate record.
- `stale_profile` — candidate profile is marked `needs_review` or clearly outdated.

## Reporting
For each batch report: mean relevance, % scored ≥3 (precision proxy), κ between annotators, and
counts for each flag. Regressions in mean relevance or a rise in `hallucinated_claim` block a
release.
