# TerraScout explorer modes (dashboard IA)

**Status:** approved (operator 2026-11-13)  
**Branch (when building):** `cursor/explorer-modes-598f` from `cursor/review-workstation-598f`  
**Supersedes (dashboard only):** MVP capability #7’s single-page “ranked queue + terrain + packet” as the product identity. Detection, CLI analyze/agents, registry, and ethics invariants are unchanged.

## Aspiration

Over time, TerraScout should help humans and a cheap agent swarm scan and analyze LiDAR/DEM coverage toward world-scale candidate discovery — always fail-closed on novelty, never claiming sites, never publishing unpublished coordinates. Swarm stays tool-first; LLM optional and unused by default.

## Scope now

- **Geography:** North America acquisition and study-area practice (existing USGS TNM/3DEP path). No multi-continent orchestration.
- **Surface:** localhost Streamlit three-mode explorer over **one analysis directory**.
- **Keep:** `CandidateStore` SQLite, local GeoTIFFs, `CandidateFeature`, `terra-scout analyze` / agents CLI, olive/amber field-console theme, ethics banner rules.

## Non-goals (this slice)

- Detector rewrite, new morphology models, VLMs, OpenAlex HTTP, Gemini reconstructions
- Re-running the swarm from the dashboard
- Viewport-cropped detection, async job queues, cloud workers
- Multi-region / world tiling or federation
- Public or hosted maps of unpublished geometry; authority email with coordinates
- Freehand polygon editor; auto-assign `expert_reviewed`

## Problem

The current Streamlit app is one page where the ranked queue is the product. That came from stacking MVP slices. An explorer needs a situation board, a terrain workbench that works without a queue, and a single-candidate investigation surface — without the software claiming a site.

## Modes

Shared chrome on every page: analysis-directory path (sidebar), ethics warning, observation_kind when known, olive/amber theme. Streamlit **multipage**. Keep `importlib.reload` for copy/review (and page helpers Streamlit may cache); see `docs/agents/learnings/2026-11-13-streamlit-stale-imports.md`.

Default land: **Briefing** after the directory loads (or empty/error stop).

### Briefing — situation board (not GIS)

- Study area / analysis directory identity
- `observation_kind`
- What was scanned (DEM/products present: layers, registry, map, report sidecars — factual inventory, not a map)
- Candidate counts by `review_status`
- Last swarm summary:
  - If `agent_traces.json` exists: structured fields (candidate count, `llm_was_used`, per-agent id + success/notes counts, link/path to `swarm_report.md`)
  - Else if only `swarm_report.md`: short excerpt + note that structured traces need an agents run
  - Else: honest empty (“no swarm run in this directory”)
- Ethics banner
- Jump: “open next unreviewed” → sets `st.session_state.selected_candidate_id` and navigates to Investigate
- **No map, no layer GIS**

### Explore — terrain-first workbench

- Identity is terrain, not the ranked queue
- Layer radio: hillshade / LRM / slope / TPI (existing labels/paths)
- Local `map.html` iframe when present (localhost only caption)
- Optional overlays of registry outlines (secondary); not a queue panel as the primary UI
- **DEM resolution:** analyze/agents write `run_manifest.json` at the run root with at least `dem_path` and `observation_kind`. Explore reads it; sidebar **DEM path** overrides if set. If still unresolved, disable bookmark and geometric detect with an explicit message (do not guess).
- **Bookmark place as candidate:** operator enters **easting/northing in the DEM CRS** (no click-map rewrite this slice) → fixed small buffer → `CandidateStore.add_candidates` with:
  - `detection_method`: `human_bookmark`
  - `feature_category`: `unknown_anomaly` (unless builder finds a better existing literal)
  - `anomaly_score`: `0.0` with score definition stating human nomination (not a residual statistic)
  - novelty bound to `observation_kind` (existing validator)
  - `review_status`: `unreviewed`
  - claim language: candidate site only
- **Run geometric detection:** button runs existing conventional detector on the **full DEM** resolved above, persists layers like analyze, refreshes Explore. Sync only. Copy must say geometric anomaly detection ≠ archaeology. **Registry rule:** delete existing rows whose `detection_method` is not `human_bookmark`, then add the new geometric candidates (bookmarks survive; geometric set refreshes; no UUID flood).
- **Handoff to Investigate:** secondary candidate selectbox (not hover-on-matplotlib) sets `st.session_state.selected_candidate_id` and navigates to Investigate

### Investigate — one candidate

- Ranked candidate picker (anomaly_score desc) — how humans pick when not deep-linked
- Evidence packet via existing `evidence_packet()` (no WKT)
- Six specialist traces from persisted `agent_traces.json` when present; empty state when analyze-only
- Novelty fail-closed display
- Human `review_status` selectbox (same statuses; `expert_reviewed` human-only help text)
- Focused terrain chip for the selection (reuse layer render); **no** full map iframe
- Loop caption as process: scan → rank → packet → human/authority (not a scheduler)

## Persistence add-on

Agents CLI / `write_report` (or adjacent) also writes `agent_traces.json` beside `swarm_report.md`. **Shape (builder call):** a JSON object wrapping SwarmReport fields the UI needs:

```json
{
  "summary": "...",
  "llm_was_used": false,
  "candidate_count": 0,
  "traces": [ /* AgentTrace objects */ ]
}
```

Dashboard reads it; does not invent traces.

## Analysis directory layouts

Two on-disk layouts already exist; the sidebar path is the **run root**:

| Layout | GIS / registry | Swarm sidecars |
|---|---|---|
| `analyze` | run root (`layers/`, `registry.sqlite3`, `map.html`) | optional `swarm_report.md` at root |
| `agents` | `products/` under run root | `swarm_report.md` + `agent_traces.json` at run root |

Loader resolves registry/layers/map from run root, else from `products/`. Briefing inventory reports which layout it resolved.

## Invariants (unchanged)

- `anomaly_score` is never P(archaeological)
- Do not label a candidate a new/undocumented site; literature miss ≠ novelty
- No unpublished coordinates off-box; no GitHub/social maps of unpublished geometry
- No excavation/trespass guidance
- `expert_reviewed` is human-only
- No OpenAlex HTTP, no 48 VLMs, no Gemini reconstructions, no emailing authorities with coords unless a later spec says so

## Testing

- TDD: loader/summary helpers, traces JSON round-trip, bookmark → registry candidate shape, evidence packet still omits WKT, page modules import cleanly
- `uv run pytest` ; `uv run ruff check src tests`
- Manual: Briefing empty/swarm/analyze-only; Explore without queue pressure; Investigate packet + empty traces

## Builder calls (settled here so planning is not blocked)

- Bookmark buffer radius default **25 m** in DEM meters (constant, easy to change)
- Multipage file layout under `src/terra_scout/dashboard/` per Streamlit conventions used by the CLI entrypoint
- Briefing “what was scanned” = presence checklist of known product filenames already produced by analyze/agents
- NA scope = copy + existing USGS path only; no new geography modules in this slice
- `run_manifest.json` + `agent_traces.json` wrapper shapes as above; bookmark UX = numeric DEM-CRS coordinates; re-detect keeps only `human_bookmark` rows

## Approval

Operator: reply **approve** (or request edits) to this written spec. Implementation (writing-plans → TDD) starts only after that yes. Do not treat grill “yes to all” as approval of this document.
