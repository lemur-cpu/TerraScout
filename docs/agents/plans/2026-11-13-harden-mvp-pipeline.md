# Harden MVP pipeline

**Goal:** Close in-scope holes in the existing TerraScout pipeline without new commands, data sources, or detectors.

**Architecture:** One analysis writer (`analyze_loaded_dem`) owns layers, GeoJSON, map, report, and SQLite. The swarm loads the DEM once and calls that writer. Registry lives next to products, not in a second settings path.

**Tech stack:** Existing Python 3.12, rasterio, pytest, typer.

**Spec:** `docs/agents/specs/2026-11-13-terrascout-mvp.md`

## Global constraints

- TDD. Incremental commits. Stage by path.
- DRY after the second duplication. YAGNI: no OpenAlex client, no second DEM download, no new CLI verbs.
- Do not weaken tests. Synthetic fixtures only.
- Core path still runs without LLM or PDAL.

## File map

- `src/terra_scout/io/dem.py` — refuse non-meter linear CRS units
- `src/terra_scout/viz/export.py` — write every computed terrain layer
- `src/terra_scout/config.py`, `.env.example` — drop unused `database_path`
- `src/terra_scout/analyze.py` — `analyze_loaded_dem` + persist
- `src/terra_scout/agents/geospatial.py` — inspect a loaded DEM
- `src/terra_scout/agents/orchestrator.py` — call the shared writer
- `src/terra_scout/agents/research.py` — optional coarse place name, fail closed
- `src/terra_scout/cli.py` — `--place-name` on `agents run`
- `src/terra_scout/eval/fixtures.py` — ridge and ditch rasters
- `src/terra_scout/detection/pipeline.py` — drop dead classify branch
- `tests/test_dem_io.py`, `tests/test_cli_analyze.py`, `tests/test_detection.py`, `tests/test_agents.py`

## Tasks

### Task 1: Fail on foot CRS units

Test: `test_load_dem_rejects_projected_foot_crs` writes EPSG:2227 (US survey feet) and expects `DemValidationError` matching `meter` or `foot`. Geographic EPSG:4326 still loads.

### Task 2: Export every computed terrain layer

Test: `test_analyze_writes_layers_geojson_preview_and_map` asserts `curvature`, `tpi`, `sky_view_factor`, and `ruggedness` GeoTIFFs exist beside hillshade/slope/LRM.

### Task 3: One registry path

Remove `Settings.database_path` and `TERRASCOUT_DATABASE_PATH`. Registry remains `output_dir / "registry.sqlite3"` next to analysis products. Test: existing analyze registry assertion still passes; grep finds no settings database path.

### Task 4: Shared analysis writer

`analyze_loaded_dem(dem, output_dir)` computes layers, detects once, exports, writes SQLite. `analyze_dem` loads then calls it. Swarm loads once, inspects that DEM, calls `analyze_loaded_dem`, then research/skeptic/verification/reporting. Test: swarm still writes six traces and `products/registry.sqlite3`; DEM is not a second detection path.

### Task 5: Linear and depression fixtures

`write_synthetic_dem(..., feature="mound"|"ridge"|"ditch"|"none")`. Tests: ridge → `linear_embankment`; ditch → `ditch_or_depression`. Negative polarity maps only to `ditch_or_depression`.

### Task 6: Optional `--place-name`

No name on a non-synthetic DEM → failed retrieval, no citations. Name present → record the coarse name, still invent no citations (OpenAlex not wired). Test both. CLI flag on `agents run`.

## Review focus

- Swarm must not call `detect_anomalies` twice.
- Foot-CRS refusal must not break EPSG:4326.
- Place-name path must not fabricate a URL or paper title.
