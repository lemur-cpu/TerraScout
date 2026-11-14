from __future__ import annotations

from terra_scout.coverage.grid import total_cell_count
from terra_scout.coverage.progress import coverage_completeness


def test_coverage_completeness_zero_when_empty() -> None:
    total = total_cell_count()
    counts = {
        "unscanned": total,
        "queued": 0,
        "running": 0,
        "scanned": 0,
        "skipped": 0,
        "failed": 0,
    }
    assert coverage_completeness(counts) == 0.0


def test_coverage_completeness_scanned_and_skipped() -> None:
    total = total_cell_count()
    scanned = 10
    skipped = 5
    counts = {
        "unscanned": total - scanned - skipped,
        "queued": 0,
        "running": 0,
        "scanned": scanned,
        "skipped": skipped,
        "failed": 0,
    }
    expected = (scanned + skipped) / total * 100.0
    assert coverage_completeness(counts) == expected


def test_coverage_completeness_ignores_queued_for_percent() -> None:
    total = total_cell_count()
    counts = {
        "unscanned": total - 3,
        "queued": 3,
        "running": 0,
        "scanned": 0,
        "skipped": 0,
        "failed": 0,
    }
    assert coverage_completeness(counts) == 0.0