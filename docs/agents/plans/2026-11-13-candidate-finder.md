# Candidate site finder (evidence packets)

**Goal:** Ranked candidate sites with evidence packets. Human confirms. Novelty fails closed when literature is not retrieved.

**Approved:** operator “both yes” — 72-hour loop as scan → rank → packet → human/authority; detection stays geometric; agents do skeptic / literature fail-closed / report.

**Non-goals:** OpenAlex HTTP, VLM detectors, authority email with coordinates, Gemini reconstructions, auto-confirm, “not in register = new site.”

## Behavior

- `CandidateFeature.novelty_status` is `synthetic_na` on fixtures, else `not_demonstrated`.
- Evidence packet lists score definition, metrics, novelty, skeptic notes. No WKT.
- Dashboard copy: Candidate site finder. Queue = candidate sites.
- Loop is the review process, not a scheduler.

## Spec

`docs/agents/specs/2026-11-13-terrascout-mvp.md`
