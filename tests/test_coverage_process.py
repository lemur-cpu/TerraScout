from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from terra_scout.coverage.grid import demo_seed_tiles
from terra_scout.coverage.index import CoverageIndex
from terra_scout.coverage.process import process_batch, process_next
from terra_scout.dashboard.acquire import AcquireResult
from terra_scout.data.usgs import DownloadLimitExceeded


def test_process_next_scanned(tmp_path: Path) -> None:
    root = tmp_path / "cov"
    index = CoverageIndex(root)
    index.init()
    tile_id = demo_seed_tiles()[0]
    index.enqueue(tile_id)
    study_dir = root / "studies" / tile_id

    with patch("terra_scout.coverage.process.acquire_and_analyze") as acquire:
        acquire.return_value = AcquireResult(
            dem_path=root / "cache" / "x.tif",
            output_dir=study_dir,
            observation_kind="usgs_3dep",
            candidate_count=3,
        )
        outcome = process_next(root, max_megabytes=5.0)

    assert outcome is not None
    assert outcome.status == "scanned"
    assert outcome.study_dir == study_dir
    counts = index.status_counts()
    assert counts["scanned"] == 1


def test_process_next_skips_on_download_limit(tmp_path: Path) -> None:
    root = tmp_path / "cov"
    index = CoverageIndex(root)
    index.init()
    tile_id = demo_seed_tiles()[0]
    index.enqueue(tile_id)
    index.enqueue(demo_seed_tiles()[1])

    with patch("terra_scout.coverage.process.acquire_and_analyze") as acquire:
        acquire.side_effect = DownloadLimitExceeded("too big")
        first = process_next(root, max_megabytes=1.0)
        second = process_next(root, max_megabytes=1.0)

    assert first is not None and first.status == "skipped"
    assert second is not None and second.status == "skipped"
    counts = index.status_counts()
    assert counts["skipped"] == 2


def test_process_batch_stops_when_queue_empty(tmp_path: Path) -> None:
    root = tmp_path / "cov"
    index = CoverageIndex(root)
    index.init()
    index.enqueue(demo_seed_tiles()[0])
    with patch("terra_scout.coverage.process.acquire_and_analyze") as acquire:
        acquire.return_value = AcquireResult(
            dem_path=root / "c.tif",
            output_dir=root / "studies" / demo_seed_tiles()[0],
            observation_kind="synthetic",
            candidate_count=0,
        )
        outcomes = process_batch(root, count=3, max_megabytes=5.0)
    assert len(outcomes) == 1