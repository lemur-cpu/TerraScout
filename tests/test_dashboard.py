from __future__ import annotations

from pathlib import Path

from terra_scout.analyze import analyze_dem


def test_dashboard_loader_reports_empty_directory(tmp_path: Path) -> None:
    from terra_scout.dashboard.loader import load_analysis_directory

    state = load_analysis_directory(tmp_path)
    assert state.status == "empty"
    assert "No analysis" in state.message


def test_dashboard_loader_reads_analyze_outputs(
    synthetic_dem_path: Path,
    tmp_path: Path,
) -> None:
    from terra_scout.dashboard.loader import load_analysis_directory

    output_dir = tmp_path / "out"
    analyze_dem(synthetic_dem_path, output_dir)
    state = load_analysis_directory(output_dir)
    assert state.status == "ok"
    assert state.candidate_count >= 1
    assert state.hillshade_png is not None
    from terra_scout.registry.store import CandidateStore

    registry = CandidateStore(output_dir / "registry.sqlite3")
    candidate = registry.list_candidates()[0]
    updated = registry.set_review_status(candidate.candidate_id, "needs_research")
    assert updated.review_status == "needs_research"
