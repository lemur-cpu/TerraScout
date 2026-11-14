from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

from terra_scout.dashboard import copy as dashboard_copy
from terra_scout.dashboard import swarm_run, swarm_studies, traces
from terra_scout.dashboard.manifest import write_run_manifest


def _write_dem(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"fake-dem")
    return path


def test_list_runnable_studies_finds_scanned_tile_with_dem(tmp_path: Path) -> None:
    coverage_root = tmp_path / "coverage"
    tile_dir = coverage_root / "tiles" / "tile_0_0"
    dem = _write_dem(tile_dir / "dem.tif")
    write_run_manifest(tile_dir, dem_path=dem, observation_kind="usgs_3dep")

    studies = swarm_studies.list_runnable_studies(coverage_root)
    assert len(studies) == 1
    assert studies[0].tile_id == "tile_0_0"
    assert studies[0].output_dir == tile_dir.resolve()
    assert studies[0].dem_path == dem.resolve()


def test_resolve_study_paths_from_output_dir(tmp_path: Path) -> None:
    study = tmp_path / "study"
    dem = _write_dem(study / "elev.tif")
    write_run_manifest(study, dem_path=dem, observation_kind="usgs_3dep")
    resolved = swarm_studies.resolve_study(study)
    assert resolved is not None
    assert resolved.dem_path == dem.resolve()
    assert resolved.output_dir == study.resolve()


def test_start_writes_swarm_run_json_with_running_pid(
    tmp_path: Path, monkeypatch
) -> None:
    study = tmp_path / "study"
    dem = _write_dem(study / "dem.tif")
    proc = MagicMock()
    proc.pid = 4242
    proc.poll.return_value = None
    popen = MagicMock(return_value=proc)
    monkeypatch.setattr(swarm_run.subprocess, "Popen", popen)

    state = swarm_run.start_swarm_run(dem, study)
    assert state["status"] == "running"
    assert state["pid"] == 4242
    assert Path(state["dem_path"]) == dem.resolve()
    assert Path(state["output_dir"]) == study.resolve()
    payload = json.loads((study / swarm_run.SWARM_RUN_FILENAME).read_text(encoding="utf-8"))
    assert payload["status"] == "running"
    assert payload["pid"] == 4242
    assert "--dem" in payload["command"]
    assert "agents" in payload["command"]
    popen.assert_called_once()


def test_start_refuses_second_concurrent_run(tmp_path: Path, monkeypatch) -> None:
    study = tmp_path / "study"
    dem = _write_dem(study / "dem.tif")
    alive = MagicMock()
    alive.pid = 111
    alive.poll.return_value = None
    monkeypatch.setattr(swarm_run.subprocess, "Popen", MagicMock(return_value=alive))
    monkeypatch.setattr(swarm_run.os, "kill", lambda *_a, **_k: None)
    first = swarm_run.start_swarm_run(dem, study)
    assert first["status"] == "running"

    def _fake_kill(pid: int, sig: int = 0) -> None:
        if pid == 111:
            return
        raise ProcessLookupError

    monkeypatch.setattr(swarm_run.os, "kill", _fake_kill)
    try:
        swarm_run.start_swarm_run(dem, study)
        raise AssertionError("expected SwarmRunError")
    except swarm_run.SwarmRunError as error:
        assert "already running" in str(error).lower()


def test_stop_marks_stopped_and_kills(tmp_path: Path, monkeypatch) -> None:
    study = tmp_path / "study"
    dem = _write_dem(study / "dem.tif")
    proc = MagicMock()
    proc.pid = 222
    proc.poll.return_value = None
    monkeypatch.setattr(swarm_run.subprocess, "Popen", MagicMock(return_value=proc))
    swarm_run.start_swarm_run(dem, study)

    killed: list[tuple[int, int]] = []

    def _kill(pid: int, sig: int = 0) -> None:
        if sig == 0:
            return
        killed.append((pid, sig))

    monkeypatch.setattr(swarm_run.os, "kill", _kill)
    monkeypatch.setattr(swarm_run.time, "sleep", lambda *_a, **_k: None)
    state = swarm_run.stop_swarm_run(study)
    assert state["status"] == "stopped"
    assert state.get("finished_at")
    assert any(sig != 0 for _, sig in killed) or proc.terminate.called or proc.kill.called


def test_refresh_dead_pid_with_traces_completed(tmp_path: Path, monkeypatch) -> None:
    study = tmp_path / "study"
    dem = _write_dem(study / "dem.tif")
    study.mkdir(parents=True, exist_ok=True)
    (study / "agent_traces.json").write_text(
        json.dumps(
            {
                "summary": "ok",
                "llm_was_used": False,
                "candidate_count": 0,
                "traces": [
                    {
                        "agent_id": "geospatial",
                        "task_id": "t1",
                        "timestamp": "2026-11-14T00:00:00Z",
                        "tool_calls": [],
                        "citations": [],
                        "failed_retrievals": [],
                        "notes": ["ok"],
                        "candidate_ids": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    swarm_run.write_swarm_run_state(
        study,
        {
            "status": "running",
            "pid": 99999,
            "dem_path": str(dem.resolve()),
            "output_dir": str(study.resolve()),
            "started_at": "2026-11-14T00:00:00Z",
            "command": ["python", "-m", "terra_scout.cli", "agents", "run"],
        },
    )

    def _dead(pid: int, sig: int = 0) -> None:
        raise ProcessLookupError

    monkeypatch.setattr(swarm_run.os, "kill", _dead)
    state = swarm_run.refresh_swarm_run(study)
    assert state["status"] == "completed"


def test_refresh_dead_pid_without_traces_failed(tmp_path: Path, monkeypatch) -> None:
    study = tmp_path / "study"
    dem = _write_dem(study / "dem.tif")
    swarm_run.write_swarm_run_state(
        study,
        {
            "status": "running",
            "pid": 99998,
            "dem_path": str(dem.resolve()),
            "output_dir": str(study.resolve()),
            "started_at": "2026-11-14T00:00:00Z",
            "command": ["python", "-m", "terra_scout.cli", "agents", "run"],
            "exit_code": 1,
        },
    )

    def _dead(pid: int, sig: int = 0) -> None:
        raise ProcessLookupError

    monkeypatch.setattr(swarm_run.os, "kill", _dead)
    state = swarm_run.refresh_swarm_run(study)
    assert state["status"] == "failed"


def test_attach_reads_existing_state(tmp_path: Path) -> None:
    study = tmp_path / "study"
    dem = _write_dem(study / "dem.tif")
    swarm_run.write_swarm_run_state(
        study,
        {
            "status": "completed",
            "pid": 1,
            "dem_path": str(dem.resolve()),
            "output_dir": str(study.resolve()),
            "started_at": "2026-11-14T00:00:00Z",
            "finished_at": "2026-11-14T00:01:00Z",
            "exit_code": 0,
            "command": [],
        },
    )
    state = swarm_run.attach_swarm_run(study)
    assert state is not None
    assert state["status"] == "completed"
    assert swarm_run.attach_swarm_run(tmp_path / "missing") is None


def test_agent_status_rows_pending_while_running() -> None:
    rows = traces.agent_status_rows(
        None,
        {"status": "running", "pid": 1},
    )
    assert [r["agent_id"] for r in rows] == traces.KNOWN_AGENT_IDS
    assert all(r["status"] in {"pending", "running"} for r in rows)
    assert sum(1 for r in rows if r["status"] == "running") <= 1


def test_agent_status_rows_done_when_traces_present() -> None:
    payload = {
        "traces": [
            {
                "agent_id": "geospatial",
                "timestamp": "2026-11-14T12:00:00Z",
                "notes": ["checked dem"],
            },
            {
                "agent_id": "detection",
                "timestamp": "2026-11-14T12:01:00Z",
                "notes": ["found candidates"],
            },
        ]
    }
    rows = traces.agent_status_rows(payload, {"status": "completed"})
    by_id = {r["agent_id"]: r for r in rows}
    assert by_id["geospatial"]["status"] == "done"
    assert by_id["detection"]["status"] == "done"
    assert by_id["research"]["status"] in {"pending", "unknown"}
    assert "checked" in (by_id["geospatial"].get("notes_preview") or "")


def test_swarm_copy_no_longer_stub() -> None:
    assert "not shipped" not in dashboard_copy.SWARM_CAPTION.lower()
    assert "not shipped" not in dashboard_copy.SWARM_BODY.lower()
    assert "stub" not in dashboard_copy.HOME_CTA_SWARM.lower()
    assert "cloud" in dashboard_copy.SWARM_BODY.lower()
    assert "no cloud" in dashboard_copy.SWARM_BODY.lower() or "there is no cloud" in (
        dashboard_copy.SWARM_BODY.lower()
    )
    assert "anomaly" in dashboard_copy.SWARM_ETHICS.lower() or "not" in (
        dashboard_copy.SWARM_ETHICS.lower()
    )
    assert "archaeolog" in dashboard_copy.SWARM_ETHICS.lower()
    assert "expert_reviewed" in dashboard_copy.SWARM_BODY.lower() or "human" in (
        dashboard_copy.SWARM_STOP_HELP.lower() + dashboard_copy.SWARM_BODY.lower()
    )
    assert "slice c" in dashboard_copy.REVIEW_CAPTION.lower()


def test_render_swarm_smoke(tmp_path: Path, monkeypatch) -> None:
    from terra_scout.dashboard import copy as copy_mod
    from terra_scout.dashboard import pages_swarm

    coverage_root = tmp_path / "coverage"
    tile_dir = coverage_root / "tiles" / "tile_1_1"
    dem = _write_dem(tile_dir / "dem.tif")
    write_run_manifest(tile_dir, dem_path=dem, observation_kind="usgs_3dep")

    class _StubStreamlit:
        def subheader(self, *_a, **_k) -> None:
            pass

        def caption(self, *_a, **_k) -> None:
            pass

        def markdown(self, *_a, **_k) -> None:
            pass

        def info(self, *_a, **_k) -> None:
            pass

        def warning(self, *_a, **_k) -> None:
            pass

        def error(self, *_a, **_k) -> None:
            pass

        def success(self, *_a, **_k) -> None:
            pass

        def button(self, *_a, **_k) -> bool:
            return False

        def selectbox(self, *_a, **_k):
            opts = _k.get("options") or (_a[1] if len(_a) > 1 else None)
            if opts:
                return opts[0]
            return None

        def dataframe(self, *_a, **_k) -> None:
            pass

        def columns(self, n: int):
            return [self for _ in range(n)]

        def rerun(self) -> None:
            pass

        def empty(self):
            return self

        def code(self, *_a, **_k) -> None:
            pass

        def write(self, *_a, **_k) -> None:
            pass

        def metric(self, *_a, **_k) -> None:
            pass

        def divider(self) -> None:
            pass

        def fragment(self, *args, **kwargs):
            def _decorator(fn):
                return fn

            if args and callable(args[0]):
                return args[0]
            return _decorator

        class _SessionState(dict):
            def __getattr__(self, name: str):
                try:
                    return self[name]
                except KeyError as error:
                    raise AttributeError(name) from error

            def __setattr__(self, name: str, value) -> None:
                self[name] = value

        session_state = _SessionState()

    stub = _StubStreamlit()
    monkeypatch.setattr(pages_swarm, "st", stub)
    pages_swarm.render_swarm(
        copy_mod,
        coverage_root=coverage_root,
        data_path=None,
        switch_scan=lambda: None,
        switch_investigate=lambda: None,
        switch_briefing=lambda: None,
    )
