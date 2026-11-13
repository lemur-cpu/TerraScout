# Explorer modes Implementation Plan

**Goal:** Rescope the Streamlit dashboard into Briefing / Explore / Investigate over one analysis directory without rewriting detection.

**Architecture:** Keep `terra-scout dashboard` → `dashboard/app.py`. Convert `app.py` into a thin shell (`st.navigation` + shared sidebar chrome). Pure helpers (loader, manifest, traces, bookmark, geometric refresh) stay unit-tested outside Streamlit; pages call those helpers.

**Tech stack:** Python 3.12+, uv, Streamlit, existing CandidateStore / analyze / agents.

**Spec:** `docs/agents/specs/2026-11-13-explorer-modes-design.md`

**Ticket:** explorer-modes

## Global constraints

- snake_case; TDD; `uv run pytest` ; `uv run ruff check src tests`
- anomaly_score ≠ P(archaeological); no new-site claims; localhost ethics
- No swarm re-run from UI; no viewport crop; NA copy only
- Branch: `cursor/explorer-modes-598f` from `cursor/review-workstation-598f`

## Review focus

- Analyze-only dir on Investigate → empty traces, not fake agents — Task 2
- Agents layout (`products/`) vs analyze root — Task 1
- Re-detect must keep `human_bookmark` rows — Task 4
- Missing DEM/manifest disables Explore actions — Task 3
- Evidence packet still omits WKT after bookmark — Task 3

## File map

| File | Responsibility |
|---|---|
| `dashboard/manifest.py` | read/write `run_manifest.json` |
| `dashboard/traces.py` | read/write `agent_traces.json` wrapper |
| `dashboard/bookmark.py` | point→25 m buffer → `CandidateFeature` |
| `dashboard/geometric.py` | full-DEM detect; replace non-bookmark registry rows |
| `dashboard/shell.py` | shared sidebar + ethics + theme hooks |
| `dashboard/pages_briefing.py` | Briefing body |
| `dashboard/pages_explore.py` | Explore body |
| `dashboard/pages_investigate.py` | Investigate body |
| `dashboard/app.py` | navigation shell; reload copy/review |
| `dashboard/loader.py` | dual layout resolve; inventory; swarm summary fields |
| `dashboard/copy.py` | mode copy (drop queue-as-product identity) |
| `registry/store.py` | `delete_where_detection_method_not(keep=...)` |
| `analyze.py` / `agents/reporting.py` | write manifest + traces sidecars |
| `tests/test_explorer_modes.py` (+ extend dashboard/registry/agents) | TDD |

---

### Task 1: Loader dual-layout + inventory + next-unreviewed

**Files:** Modify `loader.py`; Test: `tests/test_explorer_modes.py`

**Produces:** `resolve_product_root(run_root) -> Path`, extended `DashboardState` with `product_root`, `layout_kind`, `inventory: dict[str, bool]`, `next_unreviewed_id: str | None`, `swarm_summary` helpers.

- [ ] Test: agents-style fixture (`products/registry` + root `swarm_report.md`) loads candidates from `products/`
- [ ] Test: inventory keys include layers/registry/map/manifest/traces/swarm
- [ ] Test: `next_unreviewed_id` prefers first ranked unreviewed
- [ ] Implement; `uv run pytest tests/test_explorer_modes.py -q`; commit

### Task 2: `agent_traces.json` + report writer

**Files:** Create `dashboard/traces.py`; Modify `agents/reporting.py`; Test: explorer + agents tests

**Produces:** `write_agent_traces(path, *, summary, llm_was_used, candidate_count, traces) -> Path`; `load_agent_traces(path) -> dict | None`

- [ ] Test round-trip wrapper fields + AgentTrace list
- [ ] Test `write_report` creates `agent_traces.json` beside md
- [ ] Implement; pytest; commit

### Task 3: `run_manifest.json` + human bookmark

**Files:** Create `manifest.py`, `bookmark.py`; Modify `analyze.py` / swarm persist path; Test: explorer tests

**Produces:**
- `write_run_manifest(run_root, *, dem_path, observation_kind) -> Path`
- `load_run_manifest(run_root) -> dict | None`
- `resolve_dem_path(run_root, sidebar_override: str | None) -> Path | None`
- `bookmark_candidate(*, easting, northing, dem, buffer_m=25.0) -> CandidateFeature` with `detection_method="human_bookmark"`, score `0.0`, human score definition

- [ ] Test analyze writes manifest with dem path
- [ ] Test bookmark geometry buffers ~25 m; novelty follows observation_kind; packet omits WKT
- [ ] Implement; pytest; commit

### Task 4: Geometric refresh keeping bookmarks

**Files:** Modify `registry/store.py`; Create `dashboard/geometric.py`; Test: explorer + registry

**Produces:**
- `CandidateStore.delete_where_detection_method_not(self, keep: set[str]) -> int`
- `refresh_geometric_detection(*, dem_path, product_root) -> DetectionResult` — run analysis, persist layers, delete non-`human_bookmark`, add new geometric candidates

- [ ] Test: bookmark survives refresh; old geometric ids gone; new geometric present
- [ ] Implement; pytest; commit

### Task 5: Three-mode Streamlit shell + copy

**Files:** shell + three page modules + `app.py` + `copy.py`; Test: copy strings + app navigation structure (static read like existing reload test)

**Behavior:** Briefing default; Explore terrain/map/bookmark/detect; Investigate packet+traces+review; session `selected_candidate_id` handoff; shared DATA PATH + DEM override + ethics.

- [ ] Tests: copy no longer presents queue as sole product identity; app wires Briefing/Explore/Investigate; reload still before named imports
- [ ] Implement pages; pytest + ruff; commit

### Task 6: Docs + architecture note

- [ ] Mark spec **approved**; touch `docs/architecture.md` dashboard line; README dashboard blurb if present
- [ ] Commit
