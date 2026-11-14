# TerraScout operator loop (product roadmap)

**Status:** draft vision — next slices need grill + written specs before build  
**Date:** 2026-11-14  
**Builds on:** continent coverage (`2026-11-13-continent-coverage-design.md`), explorer modes, ethics

## Target experience (operator words)

1. **Home** — enter the app; one clear path into NA scanning (not a blank Briefing).
2. **Scan dashboard** — North America broken into sections; see **how complete** we are; enqueue/process progress.
3. **Swarm monitor** — a cheap agent swarm works the scanned terrain; operator watches status, not a black box.
4. **Review queue** — swarm **flags** candidates that pass research-backed qualifications; human reviews those first.
5. **Explore mode** — separate path to walk LiDAR/DEM yourself (hillshade / LRM / SVF / profiles), bookmark, dig without waiting on the swarm.

Ethics stay fixed: anomaly ≠ archaeology; novelty fail-closed; no unpublished continent pin maps; localhost; `expert_reviewed` human-only.

## What exists today (slice 0 — this PR)

| Piece | State |
|---|---|
| Coverage board (CONUS sparse tiles, seed demo, process N, % progress via status counts) | **Shipped** |
| Briefing / Explore / Investigate over one study | **Shipped** |
| Acquire one bbox | **Shipped** |
| `terra-scout agents` swarm (tool-first, optional LLM) | **Shipped as CLI**, not a live monitor UI |
| Flagged “viable” queue with research-backed qualifications | **Not shipped** (only geometric scores + human review statuses) |
| Dedicated Home screen | **Partial** (Coverage is default land, not a true Home) |
| Best-in-class LiDAR visualization | **Partial** (hillshade/LRM/slope/TPI/SVF layers; no relief shading presets, profiles, or multi-azimuth compare) |

## Visualization notes (LiDAR / DEM — research practice)

Prefer **terrain products operators already trust**, not RGB “pretty maps”:

- **Multidirectional hillshade** + optional single-azimuth scrub (relief reading)
- **Local relief / LRM** residual (mound/ditch contrast) — already primary for detection
- **Sky-view factor** and **openness** (pit/depression readability)
- **Slope / TPI** as secondary toggles
- **Vertical exaggeration** control for low-relief landscapes
- **Profile transect** across a candidate (distance vs elevation)
- Keep **outlines as candidates**, never “sites”; no public hosted geometry

Radar / SAR is **out of v1 NA path** (3DEP first). Note as future aspiration only.

## Executable slices (do in order)

### Slice A — Home + Scan completeness (small UI)

**Done when:** Home explains the loop in one screen; Coverage shows % complete (scanned+skipped / total), region chips (e.g. seed demo, custom bbox), clear CTAs: Scan · Swarm · Explore · Review.

**Depends on:** current Coverage index counts.

### Slice B — Swarm monitor (localhost)

**Done when:** From a scanned tile (or batch), operator starts/attaches swarm; live (or polled) panel shows per-agent status from `agent_traces.json` / run state; no cloud workers; stop/resume is explicit.

**Depends on:** existing agents CLI; Coverage → study handoff.

### Slice C — Flagged review queue (research-backed gates)

**Done when:** A **Review** mode lists candidates the swarm (or deterministic gates) marked `needs_research` / `potential_anthropogenic_feature` only after documented qualifications, e.g.:

- Geometric: residual score + compactness/elongation bounds (cite pipeline score definition)
- Context: not obviously road/drain via simple masks when available
- Novelty: still `not_demonstrated` until literature retrieved
- Skeptic agent notes present when swarm ran

Operator works that queue → Investigate. Software never auto-`expert_reviewed`.

**Depends on:** Slice B or analyze-only gates with honest “no swarm” labeling.

### Slice D — Explore as first-class LiDAR workbench

**Done when:** Explore is reachable from Home without Coverage; layer presets (hillshade / LRM / SVF); vertical exaggeration; optional profile tool; bookmark + geometric detect remain.

**Depends on:** existing Explore; visualization polish only.

### Slice E — Section packs (optional later)

Larger “sections” (e.g. state or 1° cells) as first-class Coverage units aggregating fine tiles — only if fine-grid UX proves too noisy.

## Non-goals until a later spec

- Cloud swarm / hosted maps of unpublished coords
- Claiming sites; auto-expert review
- Radar/SAR acquisition
- World federation beyond NA

## Next action

Operator: merge Coverage PR, then **approve Slice A** (or grill edits) as the next written mini-spec. Do not treat this roadmap as an implementation go for B–E.