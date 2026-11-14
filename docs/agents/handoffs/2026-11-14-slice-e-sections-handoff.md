# Handoff: Slice E — Section packs (optional)

Copy everything below the line into a new agent session.

---

## Mission

**Only start Slice E if the operator explicitly approves** — fine-grid Scan UX has proven too noisy and a written spec is signed off. Implement **TerraScout Slice E: Section packs** — introduce larger **sections** (e.g. US state boundaries or 1° cells) as first-class Coverage units that **aggregate** fine CONUS grid tiles for progress, enqueue, and navigation — without losing per-tile honesty for DEM work.

This is **optional later** work on the roadmap. Default action for a new agent session is **do not implement** until operator says otherwise.

## Product context

TerraScout is a **local** NA LiDAR/DEM research app (USGS 3DEP). Ethics are non-negotiable:

- Anomaly ≠ archaeology
- No unpublished continent pin maps at section scale either
- Localhost; aggregation is for **operator progress**, not public discovery maps

Operator loop: Home → **Scan** (sections + fine tiles) → Swarm → Review → Explore.

## Starting point (repo / branch)

- Repo: `https://github.com/lemur-cpu/TerraScout`
- **Base branch:** tip with Slice A Coverage board + later slices as shipped
- Create work branch: `cursor/slice-e-sections-94ce` (lowercase; prefix `cursor/`; suffix `-94ce`)
- Stack: Python 3.12+, `uv`, SQLite coverage index, Streamlit Coverage page, pytest + ruff

```bash
git fetch origin
git checkout -B cursor/slice-e-sections-94ce origin/<prior-slice-tip>
uv sync --extra dev
```

## Authoritative requirements

### Roadmap Done when (Slice E)

From `docs/agents/specs/2026-11-14-operator-loop-roadmap.md`:

> Larger “sections” (e.g. state or 1° cells) as first-class Coverage units aggregating fine tiles — only if fine-grid UX proves too noisy.

**Gating:** Operator must confirm fine-grid pain (UX note or issue) before build.

### Non-goals (Slice E)

- Replacing fine tiles with sections only (fine grid remains source of DEM paths)
- Cloud federation or hosted section maps with unpublished coords
- World beyond NA section model
- Swarm/Review/Explore rewrites (only Scan/index/navigation touch unless spec says otherwise)

### First deliverable before code

Write and land:

`docs/agents/specs/2026-11-14-slice-e-section-packs-design.md`

Include: section geometry definition (state vs 1°), mapping fine `tile_id` → section_id, aggregated status (% scanned / skipped / total), UI on Coverage (and Home completeness if needed), CLI parity with `terra-scout coverage`, migration of existing `coverage.sqlite3`, rollback story, ethics line.

Grill: boundary dataset source, CONUS-only vs AK/HI, whether enqueue is section-scoped or still tile-scoped.

Only then implement.

## What already exists (reuse — do not reimplement)

| Piece | Where |
| --- | --- |
| CONUS fine grid + sparse index | `src/terra_scout/coverage/{grid,index,process}.py` |
| Coverage CLI | `terra-scout coverage` (init, seed-demo, enqueue, process, status) |
| Dashboard Scan page | `pages_coverage.py`, default landing in `app.py` |
| Completeness helper | `coverage/progress.py` (`coverage_completeness`) |
| Design baseline | `docs/agents/specs/2026-11-13-continent-coverage-design.md` |
| Slice A Home + % complete | `docs/agents/specs/2026-11-14-slice-a-home-scan-design.md` |

Fine tiles live under `output/coverage/tiles/<tile_id>/` — sections must **reference**, not duplicate, those workspaces.

## Suggested builder shape (open to grill)

1. **Schema extension** — `sections` table or tile→section mapping; pure aggregation functions tested without Streamlit.
2. **Progress rollups** — section % from child tile status counts; same honesty as tile-level unscanned virtual cells.
3. **UI** — section picker / drill-down to fine grid; avoid continent pin map aesthetics; redact precise coords in aggregates if spec requires.
4. **CLI** — `coverage status --section` (or documented equivalent) matching dashboard.
5. **Migration** — existing installs keep working; document one-time upgrade command.

TDD for grid/aggregation; dashboard smoke tests; no network in default pytest mark.

## Process expectations

1. Confirm operator approval **before** mini-spec (this handoff is not a go signal by itself)
2. Brainstorm/grill → mini-spec → implement (TDD) → `uv run pytest -m 'not network'` + ruff
3. Push branch `cursor/slice-e-sections-94ce`; commit as you go
4. Do not merge E ahead of stable Scan UX on fine grid without operator sign-off

## Acceptance checklist

- [ ] Operator approval recorded (issue comment or spec header)
- [ ] Mini-spec committed under `docs/agents/specs/`
- [ ] Sections defined and mapped to fine tiles with tested aggregation
- [ ] Coverage UI + CLI expose section progress without hiding tile-level truth
- [ ] Home/completeness copy still accurate if wired
- [ ] Migration path documented for existing `coverage.sqlite3`
- [ ] No hosted unpublished geometry; no archaeology claims
- [ ] Tests cover aggregation + CLI/dashboard smoke; suite green excluding network
- [ ] README documents section packs vs fine tiles

## Out of scope reminder

Slice E is **optional**. If the operator has not complained about fine-grid noise, prefer polishing D or operator loop docs instead of building section packs.