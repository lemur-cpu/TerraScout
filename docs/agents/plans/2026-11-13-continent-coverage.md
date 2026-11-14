# Continent coverage board — plan

**Status:** approved (2026-11-13)

## Goal

Ship the CONUS coverage board as the dashboard default landing page, with CLI parity and unit tests for grid, sparse index, process batching, CLI, and dashboard wiring.

## Deliverables

- [x] `terra_scout.coverage.{grid,index,process}`
- [x] `coverage_cli` Typer app (`init`, `seed-demo`, `enqueue`, `process --next`, `status`)
- [x] Dashboard `pages_coverage` + `app.py` Coverage `default=True`
- [x] Tests: `test_coverage_{grid,index,process,cli,dashboard}.py`
- [x] README coverage section

## Verification

```bash
uv run pytest -m 'not network' -q
uv run ruff check src tests
```