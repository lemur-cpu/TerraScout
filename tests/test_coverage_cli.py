from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from terra_scout.cli import app
from terra_scout.coverage.grid import demo_seed_tiles, total_cell_count
from terra_scout.coverage.process import ProcessResult


def test_coverage_init_seed_status(tmp_path: Path) -> None:
    root = tmp_path / "coverage"
    runner = CliRunner()
    assert runner.invoke(app, ["coverage", "--root", str(root), "init"]).exit_code == 0
    seed = runner.invoke(app, ["coverage", "--root", str(root), "seed-demo"])
    assert seed.exit_code == 0, seed.output
    status = runner.invoke(app, ["coverage", "--root", str(root), "status"])
    assert status.exit_code == 0, status.output
    assert str(total_cell_count()) in status.output or "unscanned" in status.output.lower()
    assert (root / "coverage.sqlite3").exists()
    assert (root / "tiles").is_dir()


def test_coverage_enqueue_bbox(tmp_path: Path) -> None:
    root = tmp_path / "coverage"
    runner = CliRunner()
    runner.invoke(app, ["coverage", "--root", str(root), "init"])
    bbox = ",".join(str(v) for v in (-90.08, 38.65, -90.05, 38.67))
    result = runner.invoke(
        app,
        ["coverage", "--root", str(root), "enqueue", "--bbox", bbox],
    )
    assert result.exit_code == 0, result.output
    queued = len(demo_seed_tiles())
    assert f"Queued {queued}" in result.output or "Queued" in result.output


def test_coverage_process_requires_flag(tmp_path: Path) -> None:
    root = tmp_path / "coverage"
    runner = CliRunner()
    runner.invoke(app, ["coverage", "--root", str(root), "init"])
    result = runner.invoke(app, ["coverage", "--root", str(root), "process"])
    assert result.exit_code != 0


def test_coverage_process_next_mocked(tmp_path: Path) -> None:
    root = tmp_path / "coverage"
    runner = CliRunner()
    runner.invoke(app, ["coverage", "--root", str(root), "init"])
    tid = demo_seed_tiles()[0]
    study = root / "tiles" / tid
    with patch("terra_scout.coverage_cli.process_next") as process:
        process.return_value = [
            ProcessResult(tile_id=tid, status="scanned", study_dir=study, message=None)
        ]
        result = runner.invoke(app, ["coverage", "--root", str(root), "process", "--next"])
    assert result.exit_code == 0, result.output
    assert tid in result.output