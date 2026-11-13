from __future__ import annotations

import numpy as np
from scipy import ndimage

from terra_scout.io.dem import DigitalElevationModel
from terra_scout.provenance import ProvenanceRecord
from terra_scout.terrain.layers import TerrainLayer


def _finite_filled(elevation: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    valid = np.isfinite(elevation)
    filled = elevation.copy()
    if valid.any():
        filled[~valid] = float(np.nanmean(elevation))
    else:
        filled[:] = 0.0
    return filled, valid


def horn_gradients(dem: DigitalElevationModel) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Horn 1981 third-order finite differences. Returns dzdx, dzdy, valid mask."""
    filled, valid = _finite_filled(dem.elevation_meters)
    dx, dy = dem.cell_size_meters
    kernel_x = np.array([[-1.0, 0.0, 1.0], [-2.0, 0.0, 2.0], [-1.0, 0.0, 1.0]]) / (8.0 * dx)
    kernel_y = np.array([[1.0, 2.0, 1.0], [0.0, 0.0, 0.0], [-1.0, -2.0, -1.0]]) / (8.0 * dy)
    dzdx = ndimage.convolve(filled, kernel_x, mode="nearest")
    dzdy = ndimage.convolve(filled, kernel_y, mode="nearest")
    dzdx[~valid] = np.nan
    dzdy[~valid] = np.nan
    return dzdx, dzdy, valid


def slope_degrees(dem: DigitalElevationModel) -> TerrainLayer:
    dzdx, dzdy, _valid = horn_gradients(dem)
    slope_rad = np.arctan(np.hypot(dzdx, dzdy))
    values = np.degrees(slope_rad)
    return TerrainLayer(
        name="slope_degrees",
        values=values,
        source_dem=dem,
        provenance=ProvenanceRecord(
            source_path=dem.source_path,
            observation_kind=dem.observation_kind,
            processor="terra-scout.terrain.derivatives.slope_degrees",
            parameters={"method": "Horn1981"},
            parent_ids=["dem"],
        ),
    )


def curvature(dem: DigitalElevationModel) -> TerrainLayer:
    """Zevenbergen and Thorne 1987 profile-ish Laplacian curvature (1/m)."""
    filled, valid = _finite_filled(dem.elevation_meters)
    dx, dy = dem.cell_size_meters
    kernel = np.array(
        [
            [0.0, 1.0 / (dy**2), 0.0],
            [1.0 / (dx**2), -2.0 * (1.0 / dx**2 + 1.0 / dy**2), 1.0 / (dx**2)],
            [0.0, 1.0 / (dy**2), 0.0],
        ]
    )
    values = ndimage.convolve(filled, kernel, mode="nearest")
    values[~valid] = np.nan
    return TerrainLayer(
        name="curvature",
        values=values,
        source_dem=dem,
        provenance=ProvenanceRecord(
            source_path=dem.source_path,
            observation_kind=dem.observation_kind,
            processor="terra-scout.terrain.derivatives.curvature",
            parameters={"method": "ZevenbergenThorne1987-laplacian"},
            parent_ids=["dem"],
        ),
    )


def terrain_ruggedness_index(dem: DigitalElevationModel, window: int = 3) -> TerrainLayer:
    """Riley et al. 1999 TRI: RMS of neighborhood elevation residuals."""
    if window % 2 == 0 or window < 3:
        raise ValueError("TRI window must be an odd integer >= 3")
    filled, valid = _finite_filled(dem.elevation_meters)
    mean = ndimage.uniform_filter(filled, size=window, mode="nearest")
    variance = ndimage.uniform_filter((filled - mean) ** 2, size=window, mode="nearest")
    values = np.sqrt(np.clip(variance, 0.0, None))
    values[~valid] = np.nan
    return TerrainLayer(
        name="ruggedness",
        values=values,
        source_dem=dem,
        provenance=ProvenanceRecord(
            source_path=dem.source_path,
            observation_kind=dem.observation_kind,
            processor="terra-scout.terrain.derivatives.terrain_ruggedness_index",
            parameters={"method": "Riley1999", "window": window},
            parent_ids=["dem"],
        ),
    )
