from __future__ import annotations

from pathlib import Path

from terra_scout.io.dem import load_dem


def test_swarm_runs_six_specialists_without_an_llm_key(
    synthetic_dem_path: Path,
    tmp_path: Path,
) -> None:
    from terra_scout.agents.orchestrator import run_swarm

    report = run_swarm(
        dem_path=synthetic_dem_path,
        study_area_path=None,
        output_dir=tmp_path / "agents",
    )
    assert report.report_path.exists()
    names = [trace.agent_id for trace in report.agent_traces]
    assert names == [
        "geospatial",
        "detection",
        "research",
        "skeptic",
        "verification",
        "reporting",
    ]
    assert report.llm_was_used is False
    assert "llm_was_used=False" in report.summary
    text = report.report_path.read_text(encoding="utf-8").lower().replace("*", "")
    assert "not archaeological confirmation" in text
    assert "fabricat" not in text
    research = next(trace for trace in report.agent_traces if trace.agent_id == "research")
    assert research.failed_retrievals or research.notes
    products = tmp_path / "agents" / "products"
    assert (products / "registry.sqlite3").exists()
    assert (products / "candidates.geojson").exists()
    assert not (tmp_path / "agents" / "registry.sqlite3").exists()


def _retag_observation_kind(path: Path, kind: str) -> Path:
    import rasterio

    with rasterio.open(path, "r+") as dataset:
        dataset.update_tags(TERRASCOUT_OBSERVATION_KIND=kind)
    return path


def test_research_without_place_name_records_failed_retrieval(tmp_path: Path) -> None:
    from terra_scout.agents.research import research_context
    from terra_scout.eval.fixtures import write_synthetic_dem
    from terra_scout.io.dem import load_dem

    path = _retag_observation_kind(
        write_synthetic_dem(tmp_path / "local.tif", feature="none"),
        "local_user",
    )
    trace = research_context(load_dem(path))
    assert trace.citations == []
    assert trace.failed_retrievals
    assert "place name" in trace.failed_retrievals[0].reason.lower()
    notes = " ".join(trace.notes).lower()
    assert "novelty is not demonstrated" in notes


def test_research_with_place_name_does_not_invent_citations(tmp_path: Path) -> None:
    from terra_scout.agents.research import research_context
    from terra_scout.eval.fixtures import write_synthetic_dem
    from terra_scout.io.dem import load_dem

    path = _retag_observation_kind(
        write_synthetic_dem(tmp_path / "named.tif", feature="none"),
        "local_user",
    )
    trace = research_context(load_dem(path), place_name="Cahokia region")
    assert trace.citations == []
    notes = " ".join(trace.notes).lower()
    assert "cahokia" in notes
    assert "no citations invented" in notes or "not wired" in notes


def test_agents_run_accepts_place_name_flag(
    synthetic_dem_path: Path,
    tmp_path: Path,
) -> None:
    from typer.testing import CliRunner

    from terra_scout.cli import app

    result = CliRunner().invoke(
        app,
        [
            "agents",
            "run",
            "--dem",
            str(synthetic_dem_path),
            "--output-dir",
            str(tmp_path / "agents"),
            "--place-name",
            "Cahokia region",
        ],
    )
    assert result.exit_code == 0, result.output


def test_skeptic_records_alternative_explanations_for_candidates(
    synthetic_dem_path: Path,
) -> None:
    from terra_scout.agents.skeptic import critique_candidates
    from terra_scout.detection.pipeline import detect_anomalies

    dem = load_dem(synthetic_dem_path)
    detection = detect_anomalies(dem)
    critiques = critique_candidates(dem, detection.candidates)
    assert critiques
    assert all(item.alternative_explanations for item in critiques)
