# Plan: Slice B Swarm monitor

## Tasks

1. **Design** — land `docs/agents/specs/2026-11-14-slice-b-swarm-monitor-design.md` (this plan optional).
2. **swarm_run** — TDD: `swarm_run.json` start/attach/stop/refresh with mocked `Popen`.
3. **swarm_studies + agent_status_rows** — TDD: list scanned tiles with DEM; honest pending/done rows.
4. **UI + copy** — replace Swarm stub; Home CTA; app wiring for Investigate/Briefing; page smoke.
5. **README** — short local Swarm monitor section.
6. **Verify** — `uv run ruff check src tests` and `uv run pytest -m 'not network'`.

## Order

Design commit → run-state helpers → studies/status rows → page/copy → README → push `cursor/slice-b-swarm-94ce`.
