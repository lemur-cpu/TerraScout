from __future__ import annotations

from pathlib import Path

from terra_scout.dashboard.shell import (
    DATA_PATH_KEY,
    DATA_PATH_PENDING_KEY,
    apply_pending_data_path,
    default_data_path,
    queue_data_path,
)


def test_default_data_path_prefers_study_when_registry_exists(
    tmp_path: Path, monkeypatch
) -> None:
    study = tmp_path / "output" / "study"
    study.mkdir(parents=True)
    (study / "registry.sqlite3").write_bytes(b"")
    monkeypatch.chdir(tmp_path)
    assert default_data_path() == "output/study"


def test_default_data_path_falls_back_to_analyze(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert default_data_path() == "output/analyze"


def test_queue_then_apply_pending_data_path_updates_widget_key() -> None:
    """Acquire must not write DATA_PATH_KEY after the sidebar widget exists."""
    state: dict = {DATA_PATH_KEY: "output/analyze"}
    queue_data_path(state, "output/study")
    assert state[DATA_PATH_PENDING_KEY] == "output/study"
    assert state[DATA_PATH_KEY] == "output/analyze"
    apply_pending_data_path(state)
    assert state[DATA_PATH_KEY] == "output/study"
    assert DATA_PATH_PENDING_KEY not in state


def test_apply_pending_data_path_noop_when_absent() -> None:
    state: dict = {DATA_PATH_KEY: "output/analyze"}
    apply_pending_data_path(state)
    assert state[DATA_PATH_KEY] == "output/analyze"
