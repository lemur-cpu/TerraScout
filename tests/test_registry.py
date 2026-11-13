from __future__ import annotations

from pathlib import Path

from terra_scout.detection.pipeline import detect_anomalies
from terra_scout.io.dem import load_dem


def test_registry_round_trips_candidates_and_review_status(
    synthetic_dem_path: Path,
    tmp_path: Path,
) -> None:
    from terra_scout.registry.store import CandidateStore

    dem = load_dem(synthetic_dem_path)
    result = detect_anomalies(dem)
    store = CandidateStore(tmp_path / "registry.sqlite3")
    store.add_candidates(result.candidates)
    listed = store.list_candidates()
    assert listed
    updated = store.set_review_status(listed[0].candidate_id, "needs_research")
    assert updated.review_status == "needs_research"
    assert store.get(listed[0].candidate_id).review_status == "needs_research"
