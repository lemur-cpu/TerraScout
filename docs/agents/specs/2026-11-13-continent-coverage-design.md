# Continent coverage board — design

**Status:** approved (2026-11-13)

## Summary

TerraScout exposes a sparse SQLite index over a fixed CONUS grid. Cells are virtual until enqueued; the dashboard **Coverage** page and `terra-scout coverage` CLI share the same index and tile workspace.

## Grid

- Bounds: west −125°, south 24.5°, east −66.5°, north 49.5°.
- Cell size: 0.015° lon × 0.010° lat.
- Tile id: `c{ix}_r{iy}`.

## Index

- Database path: `{root}/coverage.sqlite3` (`CoverageIndex(path_to_sqlite_file)`).
- Virtual `unscanned` = `total_cell_count() - persisted_count()`.
- `reset_stale_running()` requeues every `running` row (no TTL).
- `enqueue(ix, iy, allow_scanned=False)`; `dequeue_queued(n)`.

## Processing

- Studies live under `{root}/tiles/{tile_id}/`.
- `process_next(index, *, n, cache_dir, max_megabytes, tiles_root)` returns `list[ProcessResult]`.
- `_pin_dem` copies the DEM into the study folder and writes `run_manifest.json`.

## Ethics

Anomaly detection is not archaeological confirmation. Do not treat absence from online inventories as evidence of an unknown site.