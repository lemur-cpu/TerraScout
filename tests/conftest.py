from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin


def write_synthetic_dem(
    path: Path,
    *,
    rows: int = 64,
    cols: int = 64,
    cell_size_meters: float = 1.0,
    origin_x: float = 500000.0,
    origin_y: float = 4_400_000.0,
    crs: str = "EPSG:32615",
    nodata: float = -9999.0,
    mound: bool = True,
) -> Path:
    """Write a projected synthetic DEM. Observation kind is synthetic, not USGS."""
    y, x = np.mgrid[0:rows, 0:cols]
    elevation = 180.0 + 0.02 * x + 0.01 * y
    if mound:
        cy, cx = rows / 2, cols / 2
        elevation = elevation + 4.0 * np.exp(-(((x - cx) ** 2 + (y - cy) ** 2) / (2 * 4.5**2)))
    elevation[0, 0] = nodata
    transform = from_origin(origin_x, origin_y, cell_size_meters, cell_size_meters)
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=rows,
        width=cols,
        count=1,
        dtype="float32",
        crs=crs,
        transform=transform,
        nodata=nodata,
    ) as dataset:
        dataset.write(elevation.astype(np.float32), 1)
        dataset.update_tags(TERRASCOUT_OBSERVATION_KIND="synthetic")
    return path


@pytest.fixture
def synthetic_dem_path(tmp_path: Path) -> Path:
    return write_synthetic_dem(tmp_path / "synthetic_mound.tif")
