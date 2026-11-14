from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from terra_scout.coverage.grid import demo_seed_tiles, total_cell_count
from terra_scout.coverage.index import CoverageIndex


def test_init_status_counts_virtual_unscanned(tmp_path: Path) -> None:
    root = tmp_path / "cov"
    index = CoverageIndex(root)
    index.init()
    counts = index.status_counts()
    assert counts["unscanned"] == total_cell_count()
    assert counts["queued"] == 0


def test_enqueue_dequeue_and_mark_scanned(tmp_path: Path) -> None:
    index = CoverageIndex(tmp_path / "cov")
    index.init()
    tile_id = demo_seed_tiles()[0]
    assert index.enqueue(tile_id)
    counts = index.status_counts()
    assert counts["queued"] == 1
    assert counts["unscanned"] == total_cell_count() - 1

    record = index.dequeue_queued()
    assert record is not None
    assert record.tile_id == tile_id
    assert record.status == "running"

    study = tmp_path / "study"
    study.mkdir()
    index.mark_status(tile_id, "scanned", study_dir=study)
    counts = index.status_counts()
    assert counts["scanned"] == 1
    assert counts["queued"] == 0
    assert not index.enqueue(tile_id)
    assert index.enqueue(tile_id, allow_scanned=True)


def test_enqueue_bbox_and_demo_seed(tmp_path: Path) -> None:
    index = CoverageIndex(tmp_path / "cov")
    index.init()
    added = index.enqueue_demo_seed()
    assert added == len(demo_seed_tiles())

    fresh = CoverageIndex(tmp_path / "cov2")
    fresh.init()
    west, south, east, north = (-90.08, 38.65, -90.05, 38.67)
    added_bbox = fresh.enqueue_bbox(west, south, east, north)
    assert added_bbox >= len(demo_seed_tiles())
    assert fresh.status_counts()["queued"] == added_bbox


def test_reset_stale_running(tmp_path: Path) -> None:
    index = CoverageIndex(tmp_path / "cov")
    index.init()
    tile_id = demo_seed_tiles()[0]
    index.enqueue(tile_id)
    index.dequeue_queued()
    stale_time = (datetime.now(UTC) - timedelta(hours=2)).replace(microsecond=0).isoformat()
    with index._connect() as conn:
        conn.execute("UPDATE tiles SET updated_at = ? WHERE tile_id = ?", (stale_time, tile_id))
        conn.commit()
    reset = index.reset_stale_running(60.0)
    assert reset == 1
    record = index.dequeue_queued()
    assert record is not None
    assert record.tile_id == tile_id