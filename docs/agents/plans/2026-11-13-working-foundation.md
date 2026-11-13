# Working foundation implementation plan

**Goal:** Ship a laptop-runnable TerraScout MVP that processes a real public DEM and keeps later phases on the same interfaces.

**Architecture:** Replaceable packages under `src/terra_scout/` — `io`, `terrain`, `detection`, `data`, `registry`, `agents`, `dashboard`, `eval`. SQLite first; PostGIS documented, not required.

**Tech stack:** Python 3.12, uv, rasterio/numpy/scipy/scikit-image, pydantic, typer, streamlit, pytest, ruff. Optional PDAL and LLM.

**Spec:** `docs/agents/specs/2026-11-13-terrascout-mvp.md`

## Global constraints

- TDD per task. Incremental commits. Stage by path.
- No secrets, raw LiDAR, or unpublished coordinates in git.
- Core path works without LLM keys and without PDAL.
- Do not weaken tests to get a green suite.

## File map

- `src/terra_scout/config.py` — settings
- `src/terra_scout/ethics.py` — coordinate redaction
- `src/terra_scout/io/dem.py` — DEM load/validate
- `src/terra_scout/terrain/*.py` — relief visualizations
- `src/terra_scout/detection/*.py` — anomaly candidates
- `src/terra_scout/data/usgs.py` — TNM + 3DEP ImageServer
- `src/terra_scout/registry/store.py` — SQLite candidates
- `src/terra_scout/agents/*.py` — typed swarm
- `src/terra_scout/dashboard/app.py` — Streamlit
- `src/terra_scout/eval/benchmark.py` — experiment harness
- `src/terra_scout/cli.py` — typer commands
- `tests/` — synthetic fixtures; `network` marker for live APIs

## Tasks

1. Scaffold and policy files (this commit family).
2. DEM load/validate + synthetic GeoTIFF fixture.
3. Terrain layers with provenance.
4. Conventional anomaly detector + GeoJSON/HTML.
5. CLI `analyze`.
6. USGS search/download with size cap.
7. Candidate registry.
8. Dashboard.
9. Agent swarm with real tools.
10. Benchmark harness + live DEM demo.

Each task: failing test → implement → `uv run pytest` → commit.
