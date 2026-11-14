# Slice B — Swarm monitor (localhost)

**Status:** approved via operator “build slice b” / Slice B mission (2026-11-14)  
**Branch:** `cursor/slice-b-swarm-94ce` from `cursor/slice-a-home-94ce`  
**Roadmap:** `2026-11-14-operator-loop-roadmap.md` Slice B  
**Handoff:** `docs/agents/handoffs/2026-11-14-slice-b-swarm-handoff.md`

## Done when

1. From a scanned Coverage tile (or DATA PATH study with a DEM), the operator can **Start** or **Attach** the local agent swarm.
2. A polled panel (~2s while a run is active) shows **per-agent status** from `swarm_run.json` run state and, when present, `agent_traces.json`.
3. **Stop** and **Resume** are explicit controls with honest UI copy (stop kills the local process; resume is Start again).
4. No cloud workers; no continent unpublished pin maps; `expert_reviewed` remains human-only.
5. Swarm page is no longer a “Slice B not shipped” stub; Home/Scan copy reflects that Swarm is available.
6. Tests cover study listing, run-state helpers, agent status rows, copy, and page smoke; suite green excluding network.
7. README notes how to use the Swarm monitor locally.

## Non-goals

- Cloud / remote worker fleet
- Fake mid-agent progress percentages or invented “live” animation
- Flagged Review queue / research gates (**Slice C**)
- Explore viz polish (**Slice D**)
- Batch multi-tile swarm in one click (picker is **single study/tile**)
- Auto-setting `expert_reviewed`
- Publishing coordinates or continent candidate maps

## Ethics line

Anomaly detection is not archaeological confirmation. Novelty stays fail-closed (`not_demonstrated` until literature is retrieved). Candidates stay on this machine; do not publish unpublished coordinates. Software never auto-sets `expert_reviewed`.

## Honesty note (traces vs run state)

The current orchestrator writes `agent_traces.json` **at the end** of a successful agents run. While a run is active:

- Show run-state status (`running` / `stopped` / `completed` / `failed`) plus known agent ids as **pending** (or at most one **running** placeholder) from run state.
- Do **not** invent mid-agent percentages.
- When `agent_traces.json` exists, show **done** for each present `agent_id` with timestamps from `AgentTrace`.

## Builder calls

### Modules

| Module | Role |
|---|---|
| `dashboard/swarm_studies.py` | List runnable studies (scanned Coverage tiles with DEM; optional DATA PATH study); resolve `dem_path` + `output_dir` |
| `dashboard/swarm_run.py` | Local subprocess lifecycle + `swarm_run.json` state |
| `dashboard/traces.py` (extend) | `KNOWN_AGENT_IDS`, `agent_status_rows(traces, run_state)` |
| `dashboard/pages_swarm.py` | Thin Streamlit UI: picker, Start/Attach/Stop/Resume, status table, CTAs |
| `dashboard/copy.py` | Real Swarm monitor copy; Home CTAs no longer say Swarm stub |
| `dashboard/app.py` | Wire Swarm sidebar + switch callbacks to Investigate / Briefing |

### CLI reuse

Start launches a **local** subprocess equivalent to:

```bash
uv run terra-scout agents run --dem <dem> --output-dir <study_dir>
```

Implementation prefers argv:

```python
[sys.executable, "-m", "terra_scout.cli", "agents", "run",
 "--dem", str(dem), "--output-dir", str(output_dir)]
```

(or the installed `terra-scout` console script — same entry as `uv run terra-scout`). No remote workers.

### Run state (`swarm_run.json` in study `output_dir`)

Fields: `status` (`running` \| `stopped` \| `completed` \| `failed`), `pid`, `dem_path`, `output_dir`, `started_at`, optional `finished_at` / `exit_code` / `command`.

- **`start_swarm_run`** — spawn subprocess; write running state; refuse a second concurrent start on the same study if the pid is still alive.
- **`attach_swarm_run`** — read existing run state / traces for a study **without** starting.
- **`stop_swarm_run`** — SIGTERM then kill if needed; mark `stopped`; do not fabricate partial `agent_traces.json`; leave any products already on disk.
- **`refresh_swarm_run`** — if status is running but pid is dead, mark `completed` (traces present) or `failed` (no traces / nonzero exit).

### UI

- Study picker: scanned Coverage tiles under the Coverage root that have a resolvable DEM (`run_manifest.json` `dem_path` or `*.tif` in the study dir), plus optional DATA PATH study when the sidebar path has a DEM.
- Show DEM path + output-dir honesty.
- Buttons: **Start**, **Attach**, **Stop**, **Resume** (Resume = Start again; copy explains re-run).
- Per-agent status table from `agent_status_rows`.
- Empty / loading / error / no-DEM states.
- Auto-refresh / fragment while a run is active (~2s); never invent progress.
- CTAs to Investigate / Briefing for the same study (queue DATA PATH via `shell.queue_data_path`).
- Keep **Back to Scan**.

### Polling vs subprocess

- Subprocess owns the agents run; Streamlit only starts/stops/attaches and polls disk state.
- Poll interval ≈ 2 seconds while `status == running`.

### Stop / resume semantics

- **Stop** = terminate the local subprocess. UI must say stop kills the process and traces appear only when a run finishes writing them.
- **Resume** = explicit Start again on the same study (re-run agents); not silent auto-restart.

### Study selection

- **Single** study/tile in Slice B (not batch).
- Coverage scanned tile under `output/coverage/tiles/<tile_id>/` **or** a DATA PATH study with DEM via `run_manifest` / GeoTIFF.

### Agent ids

`KNOWN_AGENT_IDS = ["geospatial", "detection", "research", "skeptic", "verification", "reporting"]`
