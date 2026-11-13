from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from tests.conftest import write_synthetic_dem


def test_load_dem_replaces_nodata_with_nan_and_keeps_mound_peak(synthetic_dem_path: Path) -> None:
    from terra_scout.io.dem import load_dem

    dem = load_dem(synthetic_dem_path)

    assert np.isnan(dem.elevation_meters[0, 0])
    assert dem.crs.to_epsg() == 32615
    assert dem.cell_size_meters == pytest.approx((1.0, 1.0))
    assert dem.vertical_unit == "meter"
    assert dem.observation_kind == "synthetic"
    assert float(np.nanmax(dem.elevation_meters)) > 183.0
    assert dem.provenance.source_path == synthetic_dem_path.resolve()


def test_load_dem_rejects_missing_crs(tmp_path: Path) -> None:
    from terra_scout.io.dem import DemValidationError, load_dem

    path = tmp_path / "no_crs.tif"
    array = np.ones((8, 8), dtype=np.float32)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=8,
        width=8,
        count=1,
        dtype="float32",
        transform=from_origin(0, 8, 1, 1),
        nodata=-9999,
    ) as dataset:
        dataset.write(array, 1)

    with pytest.raises(DemValidationError, match="CRS"):
        load_dem(path)


def test_load_dem_computes_meter_cell_size_from_geographic_crs(tmp_path: Path) -> None:
    from terra_scout.io.dem import load_dem

    path = tmp_path / "wgs84.tif"
    array = np.full((10, 10), 200.0, dtype=np.float32)
    # ~1 meter at this latitude is far smaller than 1 degree; we use 0.00001 deg.
    transform = from_origin(-90.06, 38.66, 0.00001, 0.00001)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=10,
        width=10,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=transform,
        nodata=-9999,
    ) as dataset:
        dataset.write(array, 1)
        dataset.update_tags(TERRASCOUT_OBSERVATION_KIND="synthetic")

    dem = load_dem(path)
    east_m, north_m = dem.cell_size_meters
    assert 0.7 < east_m < 1.3
    assert 0.9 < north_m < 1.3


def test_write_synthetic_dem_fixture_is_readable(tmp_path: Path) -> None:
    path = write_synthetic_dem(tmp_path / "check.tif", mound=False)
    with rasterio.open(path) as dataset:
        assert dataset.count == 1
        assert dataset.crs.to_epsg() == 32615
