from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from terra_scout.io.dem import load_dem


def _write_east_ramp(path: Path, slope_ratio: float = 0.1) -> Path:
    cols, rows = 32, 16
    x = np.arange(cols, dtype=np.float64)
    elevation = np.tile(100.0 + slope_ratio * x, (rows, 1))
    transform = from_origin(500000.0, 4_400_000.0, 1.0, 1.0)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=rows,
        width=cols,
        count=1,
        dtype="float32",
        crs="EPSG:32615",
        transform=transform,
        nodata=-9999,
    ) as dataset:
        dataset.write(elevation.astype(np.float32), 1)
        dataset.update_tags(TERRASCOUT_OBSERVATION_KIND="synthetic")
    return path


def test_slope_of_east_ramp_matches_arctan_of_rise_over_run(tmp_path: Path) -> None:
    from terra_scout.terrain.derivatives import slope_degrees

    dem = load_dem(_write_east_ramp(tmp_path / "ramp.tif", slope_ratio=0.1))
    slope = slope_degrees(dem)
    interior = slope[2:-2, 2:-2]
    expected = np.degrees(np.arctan(0.1))
    assert np.nanmean(interior) == pytest.approx(expected, rel=0.05)
    assert np.nanmax(interior) < expected + 1.0


def test_local_relief_is_positive_on_synthetic_mound(synthetic_dem_path: Path) -> None:
    from terra_scout.terrain.relief import local_relief_model

    dem = load_dem(synthetic_dem_path)
    residual = local_relief_model(dem, kernel_radius_pixels=8)
    peak = residual[32, 32]
    background = np.nanmedian(residual)
    assert peak > 1.0
    assert peak > background + 1.0
    assert residual.provenance.parameters["kernel_radius_pixels"] == 8


def test_multidirectional_hillshade_is_finite_and_unit_interval(
    synthetic_dem_path: Path,
) -> None:
    from terra_scout.terrain.relief import multidirectional_hillshade

    dem = load_dem(synthetic_dem_path)
    shade = multidirectional_hillshade(dem)
    valid = shade.values[np.isfinite(shade.values)]
    assert valid.size > 0
    assert valid.min() >= 0.0
    assert valid.max() <= 1.0
