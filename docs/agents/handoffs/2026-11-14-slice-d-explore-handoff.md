# Handoff: Slice D — Explore as first-class LiDAR workbench

Copy everything below the line into a new agent session.

---

## Mission

Implement **TerraScout Slice D: Explore workbench** — make **Explore** a first-class terrain path from Home (without requiring Coverage first for the documented DATA PATH flow), with trustworthy LiDAR/DEM visualization polish: layer presets (hillshade / LRM / SVF and existing secondary layers), **vertical exaggeration**, an optional **elevation profile transect** tool, while keeping bookmark + geometric detection behavior.

**Do not build Slice E.** Grill + write a mini-spec, get approval (or treat this handoff + roadmap “Done when” as the brief if the operator says “build slice d”), then implement with TDD.

## Product context

TerraScout is a **local** NA LiDAR/DEM research app (USGS 3DEP). Ethics are non-negotiable:

- Anomaly ≠ archaeology; outlines are candidates, never “sites”
- Novelty fail-closed (`not_demonstrated` until literature retrieved)
- No unpublished continent pin maps; no hosted unpublished coords
- Localhost; maps and iframes stay on this machine

Operator loop (roadmap): Home → Scan → Swarm → Review → **Explore** (parallel path: walk terrain yourself).

## Starting point (repo / branch)

- Repo: `https://github.com/lemur-cpu/TerraScout`
- **Base branch:** tip that includes Slice C (or latest shipped slice — verify Explore + Home CTAs)
- Create work branch: `cursor/slice-d-explore-94ce` (lowercase; prefix `cursor/`; suffix `-94ce`)
- Stack: Python 3.12+, `uv`, Streamlit + matplotlib/rasterio, pytest + ruff

```bash
git fetch origin
git checkout -B cursor/slice-d-explore-94ce origin/<prior-slice-tip>
uv sync --extra dev
```

## Authoritative requirements

### Roadmap Done when (Slice D)

From `docs/agents/specs/2026-11-14-operator-loop-roadmap.md`:

> Explore is reachable from Home without Coverage; layer presets (hillshade / LRM / SVF); vertical exaggeration; optional profile tool; bookmark + geometric detect remain.

Depends on: existing Explore; visualization polish only.

### Visualization notes (from roadmap — prefer operator-trusted products)

- Multidirectional hillshade + optional single-azimuth control when feasible
- **Local relief / LRM** residual (mound/ditch contrast) — primary for detection context
- **Sky-view factor** and openness where raster products exist
- Slope / TPI as secondary toggles (partially present via layer paths)
- **Vertical exaggeration** for low-relief landscapes
- **Profile transect** across a candidate (distance vs elevation)
- Keep **outlines as candidates**; no public hosted geometry

Radar / SAR is out of v1 NA path.

### Non-goals (Slice D)

- Flagged Review queue changes (**Slice C**)
- Section packs / coarse Coverage units (**Slice E**)
- Cloud tile services or continent pin maps
- Claiming sites or auto-expert review
- Full GIS desktop parity (QGIS replacement)

### First deliverable before code

Write and land:

`docs/agents/specs/2026-11-14-slice-d-explore-workbench-design.md`

Include: Done when, Non-goals, layer preset UX, how vertical exaggeration is applied (3D profile vs hillshade shading), profile tool interaction (two-point pick or manual coords), Home → Explore routing without Coverage, performance constraints for large DEMs, ethics line.

Only then implement.

## What already exists (reuse — do not reimplement)

| Piece | Where |
| --- | --- |
| Explore page | `src/terra_scout/dashboard/pages_explore.py` |
| Layer labels + candidate overlay | `src/terra_scout/dashboard/review.py` (`LAYER_LABELS`, `render_layer_with_candidates`) |
| DEM resolve + bookmark + geometric detect | `pages_explore.py`, `dashboard/geometric.py`, `bookmark.py` |
| Home CTA Explore | `pages_home.py`, `HOME_CTA_EXPLORE` in `copy.py` |
| Layer file discovery | `dashboard/loader.py` → `state.layer_paths` |
| Investigate handoff | session `selected_candidate_id` pattern in explorer modes spec |

Current layer keys in UI: hillshade, local_relief (LRM), slope_degrees, tpi — SVF may need wiring if products exist under run output dirs.

## Suggested builder shape (open to grill)

1. **Home entry** — confirm Explore opens with sidebar DATA PATH / DEM override without forcing Scan; document in copy if Coverage is optional.
2. **Presets** — radio or segmented control grouping hillshade / LRM / SVF (+ secondary); honest caption when a layer file is missing.
3. **Vertical exaggeration** — slider affecting profile plot (required) and documented effect on hillshade/LRM display (may be profile-only if 2D exaggeration is deferred — spec must say).
4. **Profile tool** — pick start/end in DEM CRS or along candidate axis; plot distance vs elevation; no coordinate export in public artifacts.
5. **Preserve** bookmark + geometric detection blocks; do not break registry semantics.

Prefer pure viz helpers + thin Streamlit; TDD for profile math and exaggeration; reuse matplotlib theme from `dashboard/theme.py`.

## Process expectations

1. Brainstorm/grill → mini-spec → implement (TDD) → `uv run pytest -m 'not network'` + ruff
2. Skills if present: verification-before-completion; agent-council before claiming done; follow session PR policy
3. Push branch `cursor/slice-d-explore-94ce`; commit as you go
4. No “pretty RGB” maps that obscure terrain reading; cite score/layer semantics in UI captions

## Acceptance checklist

- [ ] Mini-spec committed under `docs/agents/specs/`
- [ ] Explore reachable from Home per spec (Coverage not required for configured DATA PATH)
- [ ] Layer presets for hillshade / LRM / SVF (with honest missing-layer states)
- [ ] Vertical exaggeration control documented and working where spec promises
- [ ] Profile transect tool available (optional path per spec) with ethics-safe output
- [ ] Bookmark + geometric detection still work
- [ ] No continent pin map; no site claims
- [ ] Tests cover viz helpers + page smoke; suite green excluding network
- [ ] README notes Explore workbench features

## Out of scope reminder

If tempted to aggregate Coverage into state sections or build the Review queue — stop. Those are C and E. Ship Explore polish only.