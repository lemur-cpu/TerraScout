from __future__ import annotations

from terra_scout.coverage.grid import total_cell_count


def coverage_completeness(counts: dict[str, int]) -> float:
    """Fraction of CONUS grid cells scanned or skipped, as percent of total."""
    total = total_cell_count()
    if total <= 0:
        return 0.0
    done = int(counts.get("scanned", 0)) + int(counts.get("skipped", 0))
    return (done / total) * 100.0