# Handoff: Slice B — Swarm monitor (localhost)

Copy everything below the line into a new agent session.

---

## Mission

Implement **TerraScout Slice B: Swarm monitor** — replace the honest Swarm stub with a localhost panel that starts/attaches the existing agent swarm on a scanned study, shows per-agent status (live or polled), and makes stop/resume explicit. No cloud workers.

**Do not build Slice C/D.** Grill + write a mini-spec, get approval (or treat this handoff + roadmap “Done when” as the brief if the operator says “build slice b”), then implement with TDD.

## Product context

TerraScout is a **local** NA LiDAR/DEM research app (USGS 3DEP). Ethics are non-negotiable:

- Anomaly ≠ archaeology; scores are not site probability
- Novelty fail-closed (`not_demonstrated` until literature retrieved)
- No unpublished continent pin maps; no hosted unpublished coords
- Localhost; `expert_reviewed` is **human-only** (software never auto-sets it)

Operator loop (roadmap): Home → Scan → **Swarm** → Review → Explore.

## Starting point (repo / branch)

- Repo: `https://github.com/lemur-cpu/TerraScout`
- **Base branch:** `cursor/slice-a-home-94ce` (tip should include Home/Scan + Swarm stub; verify `git log -1`)
- Create work branch: `cursor/slice-b-swarm-94ce` (lowercase; prefix `cursor/`; suffix `-94ce`)
- Stack: Python 3.12+, `uv`, Streamlit multipage dashboard, pytest + ruff

```bash
git fetch origin
git checkout -B cursor/slice-b-swarm-94ce origin/cursor/slice-a-home-94ce
uv sync --extra dev
```

If Slice A is not merged to main yet, keep basing on that branch, not `main`.

## Authoritative requirements

### Roadmap Done when (Slice B)

From `docs/agents/specs/2026-11-14-operator-loop-roadmap.md`:

> From a scanned tile (or batch), operator starts/attaches swarm; live (or polled) panel shows per-agent status from `agent_traces.json` / run state; no cloud workers; stop/resume is explicit.

Depends on: existing `terra-scout agents` CLI; Coverage → study handoff.

### Non-goals (Slice B)

- Cloud / remote worker fleet
- Fake “live” UI that invents agent progress
- Auto-flagged Review queue (that is **Slice C**)
- Explore viz polish (**Slice D**)
- Publishing coordinates or continent candidate maps

### First deliverable before code

Write and land:

`docs/agents/specs/2026-11-14-slice-b-swarm-monitor-design.md`

Include: Done when, Non-goals, Builder calls (modules/CLI/UI), polling vs subprocess model, how stop/resume works, study selection (which DEM / output-dir), ethics line. Grill open decisions with the operator if anything is ambiguous (subprocess vs attach-only, poll interval, batch vs single tile).

Only then implement.

## What already exists (reuse — do not reimplement)

| Piece | Where |
|---|---|
| Agents CLI | `terra-scout agents run --dem FILE [--study-area FILE] --output-dir DIR` (`src/terra_scout/cli.py`) |
| Trace writer | `src/terra_scout/agents/trace_io.py` → `agent_traces.json` |
| Trace loader (dashboard) | `src/terra_scout/dashboard/traces.py` (`load_agent_traces`) |
| Briefing already surfaces traces | `pages_briefing.py` |
| Investigate shows specialist notes | `pages_investigate.py` |
| Coverage → per-tile study folders | `output/coverage/tiles/<tile_id>/` via `coverage/process.py` |
| Swarm **stub** page | `src/terra_scout/dashboard/pages_swarm.py` + `SWARM_*` in `copy.py` |
| Nav wiring | `app.py` — Home / Scan / Swarm / Review / Explore / Briefing / Investigate |

Correct CLI (do not regress to invalid `agents --output-dir`):

```bash
uv run terra-scout agents run --dem path/to/tile.tif --output-dir output/coverage/tiles/<tile_id>
```

## Suggested builder shape (open to grill)

1. **Study picker on Swarm** — choose a scanned Coverage tile (or DATA PATH study) that has a DEM; show path honesty.
2. **Start** — launch `agents run` as a **local** subprocess (or documented attach-to-running-output-dir); write/update under that study’s `output-dir`.
3. **Monitor** — poll `agent_traces.json` + any run/lock/state file; show per-agent name/status/timestamps; empty/loading/error states.
4. **Stop / resume** — explicit controls; never silent background forever; document what stop means (kill process vs leave partial traces).
5. **Handoff** — CTA to Investigate / Briefing for the same study; do not invent a flagged Review queue (Slice C).

Prefer pure helpers + thin Streamlit page; TDD for progress/parse/status; stub Streamlit in tests like Slice A.

## Process expectations

1. Brainstorm/grill → mini-spec → implement (TDD) → `uv run pytest -m 'not network'` + ruff
2. Skills if present: verification-before-completion; agent-council before claiming done; do not open a PR unless the operator asks (New Project / cloud rules may differ — follow the session’s PR policy)
3. Push branch `cursor/slice-b-swarm-94ce`; commit as you go
4. Keep localhost / ethics copy accurate; no fake swarm animation without real process/traces

## Acceptance checklist

- [ ] Mini-spec committed under `docs/agents/specs/`
- [ ] Swarm page is no longer a “Slice B not shipped” stub only
- [ ] Operator can start or attach swarm for a real study/DEM on localhost
- [ ] Per-agent status visible from `agent_traces.json` (and/or run state), polled or live
- [ ] Stop and resume are explicit and documented in UI copy
- [ ] No cloud workers; no continent pin map; no auto-`expert_reviewed`
- [ ] Tests cover helpers + page smoke; suite green excluding network
- [ ] README notes how to use Swarm monitor locally

## Out of scope reminder

If tempted to build a flagged candidate queue, research gates, or Explore profile tools — stop. Those are C and D. Ship one usable Swarm monitor slice.