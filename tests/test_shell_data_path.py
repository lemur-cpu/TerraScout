from __future__ import annotations

from pathlib import Path

from terra_scout.dashboard.shell import default_data_path


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
