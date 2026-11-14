from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SWARM_RUN_FILENAME = "swarm_run.json"
_AGENT_TRACES_FILENAME = "agent_traces.json"
_STOP_WAIT_SECONDS = 2.0


class SwarmRunError(RuntimeError):
    """Local swarm subprocess could not be started or controlled."""


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def swarm_run_path(output_dir: Path) -> Path:
    return Path(output_dir) / SWARM_RUN_FILENAME


def write_swarm_run_state(output_dir: Path, state: dict[str, Any]) -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = swarm_run_path(out)
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return path


def read_swarm_run_state(output_dir: Path) -> dict[str, Any] | None:
    path = swarm_run_path(Path(output_dir))
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or "status" not in payload:
        return None
    return payload


def _pid_alive(pid: int | None) -> bool:
    if pid is None or int(pid) <= 0:
        return False
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _build_agents_command(dem: Path, output_dir: Path) -> list[str]:
    return [
        sys.executable,
        "-m",
        "terra_scout.cli",
        "agents",
        "run",
        "--dem",
        str(Path(dem).resolve()),
        "--output-dir",
        str(Path(output_dir).resolve()),
    ]


def start_swarm_run(dem: Path, output_dir: Path) -> dict[str, Any]:
    dem_path = Path(dem).resolve()
    out = Path(output_dir).resolve()
    if not dem_path.is_file():
        raise SwarmRunError(f"DEM not found: {dem_path}")

    existing = read_swarm_run_state(out)
    if existing is not None and existing.get("status") == "running":
        if _pid_alive(existing.get("pid")):
            raise SwarmRunError(
                f"swarm already running for {out} (pid={existing.get('pid')})"
            )

    out.mkdir(parents=True, exist_ok=True)
    command = _build_agents_command(dem_path, out)
    # Local trusted CLI argv only (same entry as `uv run terra-scout agents run`).
    proc = subprocess.Popen(  # noqa: S603
        command,
        cwd=str(out),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    state: dict[str, Any] = {
        "status": "running",
        "pid": int(proc.pid),
        "dem_path": str(dem_path),
        "output_dir": str(out),
        "started_at": _utc_now(),
        "command": command,
    }
    write_swarm_run_state(out, state)
    return state


def attach_swarm_run(output_dir: Path) -> dict[str, Any] | None:
    state = read_swarm_run_state(Path(output_dir))
    if state is None:
        return None
    return refresh_swarm_run(Path(output_dir))


def _terminate_pid(pid: int) -> None:
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + _STOP_WAIT_SECONDS
    while time.monotonic() < deadline:
        if not _pid_alive(pid):
            return
        time.sleep(0.1)
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        return


def stop_swarm_run(output_dir: Path) -> dict[str, Any]:
    out = Path(output_dir).resolve()
    state = read_swarm_run_state(out)
    if state is None:
        raise SwarmRunError(f"no swarm run state under {out}")
    pid = state.get("pid")
    if state.get("status") == "running" and _pid_alive(pid):
        _terminate_pid(int(pid))
    state = dict(state)
    state["status"] = "stopped"
    state["finished_at"] = _utc_now()
    write_swarm_run_state(out, state)
    return state


def refresh_swarm_run(output_dir: Path) -> dict[str, Any] | None:
    out = Path(output_dir).resolve()
    state = read_swarm_run_state(out)
    if state is None:
        return None
    if state.get("status") != "running":
        return state
    if _pid_alive(state.get("pid")):
        return state

    updated = dict(state)
    traces_path = out / _AGENT_TRACES_FILENAME
    exit_code = updated.get("exit_code")
    if traces_path.exists() and (exit_code is None or int(exit_code) == 0):
        updated["status"] = "completed"
        if exit_code is None:
            updated["exit_code"] = 0
    else:
        updated["status"] = "failed"
        if exit_code is None:
            updated["exit_code"] = 1
    updated["finished_at"] = updated.get("finished_at") or _utc_now()
    write_swarm_run_state(out, updated)
    return updated
