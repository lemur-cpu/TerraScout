from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from terra_scout.analyze import analyze_dem
from terra_scout.dashboard.acquire import (
    DEMO_BBOX,
    AcquireError,
    AcquireResult,
    acquire_and_analyze,
    parse_bbox,
)
from terra_scout.dashboard.loader import load_analysis_directory


def test_parse_bbox_rejects_inverted_order() -> None:
    with pytest.raises(AcquireError, match="west < east"):
        parse_bbox(west=-90.0, south=38.0, east=-91.0, north=39.0)
    with pytest.raises(AcquireError, match="south < north"):
        parse_bbox(west=-91.0, south=39.0, east=-90.0, north=38.0)


def test_demo_bbox_matches_readme_public_box() -> None:
    assert DEMO_BBOX == (-90.070, 38.655, -90.055, 38.665)


def test_acquire_and_analyze_downloads_analyzes_and_counts(
    tmp_path: Path, synthetic_dem_path: Path
) -> None:
    cache_dir = tmp_path / "cache"
    output_dir = tmp_path / "out"
    fake_dem = cache_dir / "clip.tif"
    cache_dir.mkdir(parents=True)
    fake_dem.write_bytes(synthetic_dem_path.read_bytes())

    with (
        patch(
            "terra_scout.dashboard.acquire.download_3dep_subset",
            return_value=fake_dem,
        ) as download,
        patch("terra_scout.dashboard.acquire.load_dem") as load,
    ):
        load.return_value = MagicMock(observation_kind="usgs_3dep")
        result = acquire_and_analyze(
            west=DEMO_BBOX[0],
            south=DEMO_BBOX[1],
            east=DEMO_BBOX[2],
            north=DEMO_BBOX[3],
            cache_dir=cache_dir,
            output_dir=output_dir,
            max_megabytes=5.0,
        )

    download.assert_called_once()
    assert isinstance(result, AcquireResult)
    assert result.dem_path == fake_dem
    assert result.output_dir == output_dir
    assert result.observation_kind == "usgs_3dep"
    assert result.candidate_count >= 0
    loaded = load_analysis_directory(output_dir)
    assert loaded.status != "error"


def test_acquire_synthetic_dem_pipeline(tmp_path: Path, synthetic_dem_path: Path) -> None:
    output_dir = tmp_path / "study"
    analyze_dem(synthetic_dem_path, output_dir)
    state = load_analysis_directory(output_dir)
    assert state.status == "ok"
    assert state.candidate_count >= 0


@pytest.mark.network
def test_acquire_real_usgs_demo_bbox(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    output_dir = tmp_path / "out"
    settings_cache = cache_dir
    result = acquire_and_analyze(
        west=DEMO_BBOX[0],
        south=DEMO_BBOX[1],
        east=DEMO_BBOX[2],
        north=DEMO_BBOX[3],
        cache_dir=settings_cache,
        output_dir=output_dir,
        max_megabytes=20.0,
    )
    assert result.dem_path.exists()
    assert (output_dir / "registry.sqlite3").exists()
    state = load_analysis_directory(output_dir)
    assert state.status == "ok"
    assert result.candidate_count == state.candidate_count
