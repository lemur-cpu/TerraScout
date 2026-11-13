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
    text = report.report_path.read_text(encoding="utf-8").lower().replace("*", "")
    assert "not archaeological confirmation" in text
    assert "fabricat" not in text
    research = next(trace for trace in report.agent_traces if trace.agent_id == "research")
    assert research.failed_retrievals or research.notes


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
