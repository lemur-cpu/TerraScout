from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner


def test_analyze_writes_layers_geojson_preview_and_map(
    synthetic_dem_path: Path,
    tmp_path: Path,
) -> None:
    from terra_scout.cli import app

    output_dir = tmp_path / "out"
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["analyze", "--dem", str(synthetic_dem_path), "--output-dir", str(output_dir)],
    )
    assert result.exit_code == 0, result.output
    assert (output_dir / "layers" / "hillshade.tif").exists()
    assert (output_dir / "layers" / "slope_degrees.tif").exists()
    assert (output_dir / "layers" / "local_relief.tif").exists()
    assert (output_dir / "candidates.geojson").exists()
    assert (output_dir / "preview_hillshade.png").exists()
    assert (output_dir / "map.html").exists()
    assert (output_dir / "registry.sqlite3").exists()
    from terra_scout.registry.store import CandidateStore

    stored = CandidateStore(output_dir / "registry.sqlite3").list_candidates()
    assert stored
    assert stored[0].review_status == "unreviewed"
    geojson_text = (output_dir / "candidates.geojson").read_text(encoding="utf-8")
    assert "mound_like" in geojson_text
    assert "not a calibrated archaeological probability" in geojson_text
