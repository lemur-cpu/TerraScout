# Handoff: Slice C — Flagged review queue (research-backed gates)

Copy everything below the line into a new agent session.

---

## Mission

Implement **TerraScout Slice C: Flagged review queue** — replace the honest Review stub with a **Review** mode that lists candidates marked `needs_research` or `potential_anthropogenic_feature` only after documented qualification gates (geometric scores, simple context masks when available, novelty fail-closed, honest swarm vs analyze-only labeling). Operator works that queue → **Investigate**. Software never auto-sets `expert_reviewed`.

**Do not build Slice D/E.** Grill + write a mini-spec, get approval (or treat this handoff + roadmap “Done when” as the brief if the operator says “build slice c”), then implement with TDD.

## Product context

TerraScout is a **local** NA LiDAR/DEM research app (USGS 3DEP). Ethics are non-negotiable:

- Anomaly ≠ archaeology; scores are not site probability
- Novelty fail-closed (`not_demonstrated` until literature retrieved)
- No unpublished continent pin maps; no hosted unpublished coords
- Localhost; `expert_reviewed` is **human-only** (software never auto-sets it)

Operator loop (roadmap): Home → Scan → Swarm → **Review** → Explore.

## Starting point (repo / branch)

- Repo: `https://github.com/lemur-cpu/TerraScout`
- **Base branch:** tip that includes Slice B swarm monitor (or `cursor/slice-a-home-94ce` if B not merged yet — verify `git log` and Swarm page state)
- Create work branch: `cursor/slice-c-review-94ce` (lowercase; prefix `cursor/`; suffix `-94ce`)
- Stack: Python 3.12+, `uv`, Streamlit multipage dashboard, pytest + ruff

```bash
git fetch origin
git checkout -B cursor/slice-c-review-94ce origin/<slice-b-or-a-tip>
uv sync --extra dev
```

## Authoritative requirements

### Roadmap Done when (Slice C)

From `docs/agents/specs/2026-11-14-operator-loop-roadmap.md`:

> A **Review** mode lists candidates the swarm (or deterministic gates) marked `needs_research` / `potential_anthropogenic_feature` only after documented qualifications, e.g.:
>
> - Geometric: residual score + compactness/elongation bounds (cite pipeline score definition)
> - Context: not obviously road/drain via simple masks when available
> - Novelty: still `not_demonstrated` until literature retrieved
> - Skeptic agent notes present when swarm ran
>
> Operator works that queue → Investigate. Software never auto-`expert_reviewed`.

Depends on: Slice B or analyze-only gates with honest “no swarm” labeling.

### Non-goals (Slice C)

- Auto-`expert_reviewed` or claiming sites from queue rank
- Cloud review / shared candidate maps
- Explore viz polish (**Slice D**)
- Section-level Coverage aggregation (**Slice E**)
- Publishing coordinates or continent candidate maps

### First deliverable before code

Write and land:

`docs/agents/specs/2026-11-14-slice-c-flagged-review-design.md`

Include: Done when, Non-goals, qualification rules (deterministic vs swarm-sourced), how gates set or surface statuses, queue sort/filter, handoff to Investigate, ethics line. Grill open decisions (which fields gate `potential_anthropogenic_feature`, road/drain mask availability, cross-tile queue vs per-study).

Only then implement.

## What already exists (reuse — do not reimplement)

| Piece | Where |
| --- | --- |
| Review **stub** page | `src/terra_scout/dashboard/pages_review.py` + `REVIEW_*` in `copy.py` |
| Investigate + human review_status | `pages_investigate.py`, `REVIEW_STATUSES` |
| Registry + statuses | `src/terra_scout/registry/store.py`, `detection/models.py` (`ReviewStatus`) |
| Candidate ranking / evidence packet | `src/terra_scout/dashboard/review.py` |
| Briefing status counts | `pages_briefing.py` |
| Agent traces / skeptic notes | `dashboard/traces.py`, Investigate skeptic panel |
| Nav wiring | `app.py` — Home / Scan / Swarm / Review / Explore / Briefing / Investigate |

Statuses today (human-set in Investigate; gates may **propose** or **filter**, not auto-expert):

`unreviewed`, `likely_natural`, `likely_modern`, `needs_research`, `potential_anthropogenic_feature`, `expert_reviewed`, `rejected` — see `docs/ethics.md`.

## Suggested builder shape (open to grill)

1. **Queue source** — load candidates from local `registry.sqlite3` (per product root / study scope documented in spec).
2. **Qualification layer** — pure functions: geometric thresholds on `anomaly_score`, `circularity`, `elongation` (cite `anomaly_score_definition`); optional context flags; require `novelty_status` fail-closed; if swarm ran, surface whether skeptic traces exist — label analyze-only honestly.
3. **Review UI** — ranked/filtered list of qualified rows; show gate reasons (not archaeology labels); CTA opens Investigate with `selected_candidate_id` handoff (match explorer-modes pattern).
4. **No auto promotion** — gates may suggest status copy or filter; human still sets `expert_reviewed` in Investigate only.
5. **Empty states** — no qualified flags, no registry, no swarm traces (explain analyze-only path).

Prefer pure gate helpers + thin Streamlit page; TDD for gate logic; stub Streamlit in tests like prior slices.

## Process expectations

1. Brainstorm/grill → mini-spec → implement (TDD) → `uv run pytest -m 'not network'` + ruff
2. Skills if present: verification-before-completion; agent-council before claiming done; follow session PR policy
3. Push branch `cursor/slice-c-review-94ce`; commit as you go
4. Keep localhost / ethics copy accurate; queue is not a discovery claim

## Acceptance checklist

- [ ] Mini-spec committed under `docs/agents/specs/`
- [ ] Review page is no longer a “Slice C not shipped” stub only
- [ ] Queue lists only candidates passing documented qualification gates (or clearly labeled analyze-only subset)
- [ ] Gate reasons visible; novelty and skeptic labeling honest
- [ ] Operator can open Investigate from a queue row for human review
- [ ] No auto-`expert_reviewed`; no continent pin map; no cloud queue
- [ ] Tests cover gate helpers + page smoke; suite green excluding network
- [ ] README notes Review queue behavior locally

## Out of scope reminder

If tempted to build profile tools, layer presets, or state-level Coverage packs — stop. Those are D and E. Ship one usable research-gated Review queue.