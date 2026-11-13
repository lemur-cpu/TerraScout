# TerraScout agent rules

This file governs future Cursor sessions. It does not replace `docs/agents/specs/` or `docs/agents/plans/`.

## Mission

TerraScout is an evidence-driven remote-sensing research system. Anomaly detection is not archaeological confirmation. Do not claim discovery. Do not train or advertise an archaeological ML model without labeled data, a training run, and evaluation.

## How to work

1. Read this file, `docs/architecture.md`, and the active plan before editing.
2. Test-driven development: failing test first, watch it fail, then implement.
3. Incremental commits: one coherent slice per commit, staged by explicit path. Never `git add -A`.
4. Commit messages explain *why*. Prefer `type(scope): summary`.
5. Fail fast. Raise explicit errors; do not swallow GIS, CRS, nodata, or download failures.
6. YAGNI and DRY after the second duplication. Prefer replaceable module interfaces.
7. Python identifiers use snake_case. Types and Pydantic models use PascalCase.

## Branching

Cloud agent branches use `cursor/<descriptive-name>-598f`. Do not commit to `main`. Do not force-push.

## Data and ethics

- Never commit raw LiDAR, large rasters, model weights, API keys, or precise unpublished site coordinates.
- Keep candidate geometry in the local SQLite registry (gitignored). Redact coordinates in logs, LLM prompts, and public HTML by default.
- `TERRASCOUT_SEND_PRECISE_COORDINATES_TO_LLM` defaults to false. Do not change that default.
- Do not generate excavation, trespass, or artifact-removal instructions.
- Absence from online inventories is not evidence that a place is unknown to archaeologists or Indigenous communities.
- Agent agreement is not independent scientific evidence.

## Runtime constraints

- Core DEM analysis must run without an LLM API key and without PDAL.
- Never auto-download more than `TERRASCOUT_MAX_DOWNLOAD_MEGABYTES`.
- DEM-only workflows are first-class. Point-cloud steps are optional and must degrade with a clear error.
- Synthetic fixtures and live USGS observations must stay labeled as such.

## Commands

```bash
uv sync --extra dev
uv run ruff check src tests
uv run pytest
uv run terra-scout analyze --dem path/to/dem.tif --output-dir output/demo
uv run terra-scout dashboard
```

## Review bar

Do not skip tests, loosen numeric tolerances, or add `# noqa` without a one-line reason. Verification requires a fresh command, not an earlier run.
