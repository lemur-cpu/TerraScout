from __future__ import annotations

from pathlib import Path

from terra_scout.coverage.grid import demo_seed_tiles, parse_tile_id, total_cell_count
from terra_scout.coverage.index import CoverageIndex


def _db(root: Path) -> CoverageIndex:
    path = root / "coverage.sqlite3"
    index = CoverageIndex(path)
    index.ensure_open()
    return index


def test_init_status_counts_virtual_unscanned(tmp_path: Path) -> None:
    index = _db(tmp_path / "cov")
    counts = index.status_counts()
    assert counts["unscanned"] == total_cell_count()
    assert counts["queued"] == 0
    assert index.persisted_count() == 0


def test_enqueue_dequeue_and_mark_scanned(tmp_path: Path) -> None:
    index = _db(tmp_path / "cov")
    first_tid = demo_seed_tiles()[0]
    ix, iy = parse_tile_id(first_tid)
    assert index.enqueue(ix, iy)
    counts = index.status_counts()
    assert counts["queued"] == 1
    assert counts["unscanned"] == total_cell_count() - 1

    records = index.dequeue_queued(1)
    assert len(records) == 1
    assert records[0].tile_id == first_tid
    assert records[0].status == "running"

    study = tmp_path / "tiles" / first_tid
    study.mkdir(parents=True)
    index.mark_status(first_tid, "scanned", study_dir=study)
    counts = index.status_counts()
    assert counts["scanned"] == 1
    assert counts["queued"] == 0
    assert not index.enqueue(ix, iy)
    assert index.enqueue(ix, iy, allow_scanned=True)


def test_enqueue_bbox_and_demo_seed(tmp_path: Path) -> None:
    index = _db(tmp_path / "cov")
    added = index.enqueue_demo_seed()
    assert added == len(demo_seed_tiles())

    fresh = _db(tmp_path / "cov2")
    west, south, east, north = (-90.08, 38.65, -90.05, 38.67)
    added_bbox = fresh.enqueue_bbox(west, south, east, north)
    assert added_bbox >= len(demo_seed_tiles())
    assert fresh.status_counts()["queued"] == added_bbox


def test_reset_stale_running(tmp_path: Path) -> None:
    index = _db(tmp_path / "cov")
    first_tid = demo_seed_tiles()[0]
    ix, iy = parse_tile_id(first_tid)
    index.enqueue(ix, iy)
    index.dequeue_queued(1)
    reset = index.reset_stale_running()
    assert reset == 1
    records = index.dequeue_queued(1)
    assert len(records) == 1
    assert records[0].tile_id == first_tid


def test_skip_persists_skipped_row(tmp_path: Path) -> None:
    index = _db(tmp_path / "cov")
    ix, iy = parse_tile_id(demo_seed_tiles()[0])
    assert index.skip(ix, iy, message="manual")
    assert index.status_counts()["skipped"] == 1