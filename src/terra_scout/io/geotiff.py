from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from rasterio.crs import CRS as RasterioCrs

from terra_scout.io.dem import DigitalElevationModel
from terra_scout.terrain.layers import TerrainLayer


def write_layer_geotiff(layer: TerrainLayer, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    dem = layer.source_dem
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=layer.values.shape[0],
        width=layer.values.shape[1],
        count=1,
        dtype="float32",
        crs=RasterioCrs.from_wkt(dem.crs.to_wkt()),
        transform=dem.transform,
        nodata=np.nan,
    ) as dataset:
        dataset.write(layer.values.astype(np.float32), 1)
        dataset.update_tags(
            TERRASCOUT_LAYER=layer.name,
            TERRASCOUT_PROCESSOR=layer.provenance.processor,
            TERRASCOUT_OBSERVATION_KIND=dem.observation_kind,
        )
    return path


def write_dem_geotiff(dem: DigitalElevationModel, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=dem.elevation_meters.shape[0],
        width=dem.elevation_meters.shape[1],
        count=1,
        dtype="float32",
        crs=RasterioCrs.from_wkt(dem.crs.to_wkt()),
        transform=dem.transform,
        nodata=np.nan,
    ) as dataset:
        dataset.write(dem.elevation_meters.astype(np.float32), 1)
        dataset.update_tags(TERRASCOUT_OBSERVATION_KIND=dem.observation_kind)
    return path
