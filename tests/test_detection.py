from __future__ import annotations

from pathlib import Path

from terra_scout.io.dem import load_dem


def test_synthetic_mound_is_detected_as_mound_like(synthetic_dem_path: Path) -> None:
    from terra_scout.detection.pipeline import detect_anomalies

    dem = load_dem(synthetic_dem_path)
    result = detect_anomalies(dem)
    mounds = [c for c in result.candidates if c.feature_category == "mound_like"]
    assert mounds, "expected the synthetic Gaussian mound to be a candidate"
    best = max(mounds, key=lambda candidate: candidate.anomaly_score)
    assert best.anomaly_score > 1.0
    assert best.anomaly_score_definition.startswith("residual")
    assert "not a calibrated archaeological probability" in best.anomaly_score_definition.lower()
    assert best.review_status == "unreviewed"
    assert best.observation_kind == "synthetic"


def test_flat_dem_does_not_invent_mounds(tmp_path: Path) -> None:
    from terra_scout.detection.pipeline import detect_anomalies
    from terra_scout.io.dem import load_dem
    from tests.conftest import write_synthetic_dem

    path = write_synthetic_dem(tmp_path / "flat.tif", mound=False)
    dem = load_dem(path)
    result = detect_anomalies(dem)
    assert all(candidate.feature_category != "mound_like" for candidate in result.candidates)
