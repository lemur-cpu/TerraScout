from __future__ import annotations

from pathlib import Path


class PointCloudUnavailable(RuntimeError):
    """PDAL is optional. DEM-only workflows must still run."""


def require_pdal() -> None:
    try:
        import pdal  # noqa: F401
    except ImportError as error:
        raise PointCloudUnavailable(
            "PDAL is not installed. Continue with a DEM GeoTIFF, or install the "
            "optional extra: `uv sync --extra lidar` plus a system PDAL build."
        ) from error


def ept_pipeline_spec(ept_url: str, polygon_wkt: str, output_laz: Path) -> dict:
    require_pdal()
    return {
        "pipeline": [
            {"type": "readers.ept", "filename": ept_url, "polygon": polygon_wkt},
            {"type": "filters.range", "limits": "Classification[2:2]"},
            {"type": "writers.gdal", "filename": str(output_laz.with_suffix(".tif"))},
        ]
    }
