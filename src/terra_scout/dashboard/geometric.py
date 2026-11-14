from __future__ import annotations

from pathlib import Path

from terra_scout.analyze import persist_analysis, run_analysis
from terra_scout.detection.models import DetectionResult
from terra_scout.io.dem import load_dem
from terra_scout.registry.store import CandidateStore

HUMAN_BOOKMARK_METHOD = "human_bookmark"


def refresh_geometric_detection(
    *,
    dem_path: Path,
    product_root: Path,
) -> DetectionResult:
    """Re-run conventional detection on a DEM; keep human_bookmark rows."""
    dem = load_dem(dem_path)
    layers, detection = run_analysis(dem)
    registry = CandidateStore(product_root / "registry.sqlite3")
    registry.delete_where_detection_method_not(keep={HUMAN_BOOKMARK_METHOD})
    persist_analysis(dem, layers, detection, product_root)
    return detection
