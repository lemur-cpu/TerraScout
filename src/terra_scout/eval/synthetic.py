from __future__ import annotations

from pathlib import Path

from shapely.geometry import Point, mapping

from terra_scout.eval.fixtures import write_synthetic_dem


def build_synthetic_case(directory: Path) -> tuple[Path, dict]:
    """Labeled synthetic mound. Not a scientific observation."""
    dem_path = write_synthetic_dem(directory / "synthetic_mound.tif")
    # Peak is at pixel (32, 32) on a 64x64, 1 m grid originating at 500000, 4400000
    ground_truth = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"category": "mound_like", "observation_kind": "synthetic"},
                "geometry": mapping(Point(500000.0 + 32.5, 4_400_000.0 - 32.5).buffer(6.0)),
            }
        ],
    }
    return dem_path, ground_truth
