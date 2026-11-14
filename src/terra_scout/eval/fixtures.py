from __future__ import annotations

from pathlib import Path
from typing import Literal

import numpy as np
import rasterio
from rasterio.transform import from_origin

SyntheticFeature = Literal["mound", "ridge", "ditch", "none"]


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
    feature: SyntheticFeature = "mound",
) -> Path:
    """Write a projected synthetic DEM. Observation kind is synthetic, not USGS."""
    y, x = np.mgrid[0:rows, 0:cols]
    elevation = 180.0 + 0.02 * x + 0.01 * y
    if feature == "mound":
        cy, cx = rows / 2, cols / 2
        elevation = elevation + 4.0 * np.exp(-(((x - cx) ** 2 + (y - cy) ** 2) / (2 * 4.5**2)))
    elif feature == "ridge":
        cy = rows / 2
        along = (x >= 6) & (x < cols - 6)
        elevation = elevation + 4.5 * np.exp(-((y - cy) ** 2) / (2 * 1.15**2)) * along
    elif feature == "ditch":
        cy = rows / 2
        along = (x >= 6) & (x < cols - 6)
        elevation = elevation - 4.5 * np.exp(-((y - cy) ** 2) / (2 * 1.15**2)) * along
    elif feature != "none":
        raise ValueError(f"unsupported synthetic feature: {feature}")
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
