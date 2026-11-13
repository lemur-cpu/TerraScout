from __future__ import annotations

import numpy as np
from scipy import ndimage

from terra_scout.io.dem import DigitalElevationModel
from terra_scout.provenance import ProvenanceRecord
from terra_scout.terrain.derivatives import _finite_filled, horn_gradients
from terra_scout.terrain.layers import TerrainLayer

DEFAULT_HILLSHADE_AZIMUTHS = (225.0, 270.0, 315.0, 360.0)


def _aspect_radians(dzdx: np.ndarray, dzdy: np.ndarray) -> np.ndarray:
    return np.arctan2(dzdy, -dzdx)


def hillshade(
    dem: DigitalElevationModel,
    *,
    azimuth_degrees: float = 315.0,
    altitude_degrees: float = 45.0,
) -> TerrainLayer:
    """Horn-based hillshade, unit interval. ESRI-style illumination."""
    dzdx, dzdy, valid = horn_gradients(dem)
    slope = np.arctan(np.hypot(dzdx, dzdy))
    aspect = _aspect_radians(dzdx, dzdy)
    zenith = np.radians(90.0 - altitude_degrees)
    azimuth = np.radians(azimuth_degrees)
    shaded = (np.cos(zenith) * np.cos(slope)) + (
        np.sin(zenith) * np.sin(slope) * np.cos(azimuth - aspect)
    )
    values = np.clip(shaded, 0.0, 1.0)
    values[~valid] = np.nan
    return TerrainLayer(
        name="hillshade",
        values=values,
        source_dem=dem,
        provenance=ProvenanceRecord(
            source_path=dem.source_path,
            observation_kind=dem.observation_kind,
            processor="terra-scout.terrain.relief.hillshade",
            parameters={
                "azimuth_degrees": azimuth_degrees,
                "altitude_degrees": altitude_degrees,
                "method": "Horn1981",
            },
            parent_ids=["dem"],
        ),
    )


def multidirectional_hillshade(
    dem: DigitalElevationModel,
    azimuths: tuple[float, ...] = DEFAULT_HILLSHADE_AZIMUTHS,
    altitude_degrees: float = 45.0,
) -> TerrainLayer:
    """Mean of several directional hillshades (RVT-style multi-hillshade)."""
    stack = [
        hillshade(dem, azimuth_degrees=azimuth, altitude_degrees=altitude_degrees).values
        for azimuth in azimuths
    ]
    stacked = np.stack(stack, axis=0)
    finite_count = np.sum(np.isfinite(stacked), axis=0)
    values = np.nansum(stacked, axis=0) / np.maximum(finite_count, 1)
    values[finite_count == 0] = np.nan
    return TerrainLayer(
        name="hillshade",
        values=values,
        source_dem=dem,
        provenance=ProvenanceRecord(
            source_path=dem.source_path,
            observation_kind=dem.observation_kind,
            processor="terra-scout.terrain.relief.multidirectional_hillshade",
            parameters={
                "azimuths": list(azimuths),
                "altitude_degrees": altitude_degrees,
            },
            parent_ids=["dem"],
        ),
    )


def local_relief_model(
    dem: DigitalElevationModel,
    kernel_radius_pixels: int = 12,
) -> TerrainLayer:
    """Hesse 2010-style residual: elevation minus circular mean trend."""
    if kernel_radius_pixels < 1:
        raise ValueError("kernel_radius_pixels must be >= 1")
    filled, valid = _finite_filled(dem.elevation_meters)
    diameter = kernel_radius_pixels * 2 + 1
    radius = kernel_radius_pixels
    y, x = np.ogrid[-radius : radius + 1, -radius : radius + 1]
    kernel = (x * x + y * y <= kernel_radius_pixels * kernel_radius_pixels).astype(np.float64)
    kernel /= kernel.sum()
    trend = ndimage.convolve(filled, kernel, mode="nearest")
    values = dem.elevation_meters - trend
    values[~valid] = np.nan
    return TerrainLayer(
        name="local_relief",
        values=values,
        source_dem=dem,
        provenance=ProvenanceRecord(
            source_path=dem.source_path,
            observation_kind=dem.observation_kind,
            processor="terra-scout.terrain.relief.local_relief_model",
            parameters={
                "method": "Hesse2010-circular-mean",
                "kernel_radius_pixels": kernel_radius_pixels,
                "kernel_diameter_pixels": diameter,
            },
            parent_ids=["dem"],
        ),
    )


def multiscale_tpi(
    dem: DigitalElevationModel,
    radii_pixels: tuple[int, ...] = (3, 9, 21),
) -> TerrainLayer:
    """Weiss 2001 TPI averaged over several neighborhood radii."""
    filled, valid = _finite_filled(dem.elevation_meters)
    scales = []
    for radius in radii_pixels:
        diameter = radius * 2 + 1
        mean = ndimage.uniform_filter(filled, size=diameter, mode="nearest")
        scales.append(filled - mean)
    values = np.mean(np.stack(scales, axis=0), axis=0)
    values[~valid] = np.nan
    return TerrainLayer(
        name="tpi",
        values=values,
        source_dem=dem,
        provenance=ProvenanceRecord(
            source_path=dem.source_path,
            observation_kind=dem.observation_kind,
            processor="terra-scout.terrain.relief.multiscale_tpi",
            parameters={"method": "Weiss2001", "radii_pixels": list(radii_pixels)},
            parent_ids=["dem"],
        ),
    )


def sky_view_factor(
    dem: DigitalElevationModel,
    n_directions: int = 8,
    radius_pixels: int = 8,
) -> TerrainLayer:
    """Zakšek et al. 2011 SVF approximation with discrete horizon search."""
    filled, valid = _finite_filled(dem.elevation_meters)
    dx, dy = dem.cell_size_meters
    cell = float(min(dx, dy))
    rows, cols = filled.shape
    horizons = np.zeros((n_directions, rows, cols), dtype=np.float64)
    for direction_index in range(n_directions):
        angle = 2.0 * np.pi * direction_index / n_directions
        step_x = np.sin(angle)
        step_y = -np.cos(angle)
        max_slope = np.zeros((rows, cols), dtype=np.float64)
        for distance in range(1, radius_pixels + 1):
            sample = ndimage.shift(
                filled,
                shift=(distance * step_y, distance * step_x),
                order=1,
                mode="nearest",
            )
            rise = sample - filled
            run = distance * cell
            max_slope = np.maximum(max_slope, rise / run)
        horizons[direction_index] = np.arctan(max_slope)
    values = 1.0 - np.mean(np.sin(np.clip(horizons, 0.0, np.pi / 2.0)), axis=0)
    values[~valid] = np.nan
    return TerrainLayer(
        name="sky_view_factor",
        values=values,
        source_dem=dem,
        provenance=ProvenanceRecord(
            source_path=dem.source_path,
            observation_kind=dem.observation_kind,
            processor="terra-scout.terrain.relief.sky_view_factor",
            parameters={
                "method": "Zaksek2011-discrete-horizon",
                "n_directions": n_directions,
                "radius_pixels": radius_pixels,
            },
            parent_ids=["dem"],
        ),
    )
