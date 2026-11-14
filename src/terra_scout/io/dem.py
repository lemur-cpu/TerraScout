from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from pyproj import CRS, Geod
from rasterio.transform import Affine, array_bounds

from terra_scout.provenance import ObservationKind, ProvenanceRecord


class DemValidationError(ValueError):
    """DEM is missing CRS, units, or a usable elevation band."""


@dataclass(frozen=True)
class DigitalElevationModel:
    elevation_meters: NDArray[np.float64]
    transform: Affine
    crs: CRS
    nodata: float | None
    vertical_unit: str
    source_path: Path | None
    provenance: ProvenanceRecord
    cell_size_meters: tuple[float, float]

    @property
    def observation_kind(self) -> ObservationKind:
        return self.provenance.observation_kind

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        rows, cols = self.elevation_meters.shape
        return array_bounds(rows, cols, self.transform)

    @property
    def valid_fraction(self) -> float:
        total = self.elevation_meters.size
        if total == 0:
            return 0.0
        return float(np.isfinite(self.elevation_meters).sum() / total)


def load_dem(path: Path | str) -> DigitalElevationModel:
    """Load a single-band DEM, convert nodata to NaN, and record provenance."""
    import rasterio

    source_path = Path(path).resolve()
    if not source_path.exists():
        raise DemValidationError(f"DEM file does not exist: {source_path}")

    with rasterio.open(source_path) as dataset:
        if dataset.count < 1:
            raise DemValidationError("DEM has no raster bands")
        if dataset.crs is None:
            raise DemValidationError("DEM is missing a CRS; refuse to guess")
        raster_crs = CRS.from_user_input(dataset.crs)
        elevation = dataset.read(1, masked=True)
        nodata = dataset.nodata
        transform = dataset.transform
        tags = dataset.tags()

    elevation_meters = np.array(elevation.filled(np.nan), dtype=np.float64)
    if not np.isfinite(elevation_meters).any():
        raise DemValidationError("DEM contains no finite elevation samples")

    _refuse_non_meter_linear_units(raster_crs)
    cell_size_meters = _cell_size_meters(transform, raster_crs, elevation_meters.shape)
    observation_kind = _observation_kind(tags)
    provenance = ProvenanceRecord(
        source_path=source_path,
        observation_kind=observation_kind,
        parameters={
            "driver": "GTiff",
            "width": int(elevation_meters.shape[1]),
            "height": int(elevation_meters.shape[0]),
            "crs": raster_crs.to_wkt(),
            "nodata": nodata,
        },
    )
    return DigitalElevationModel(
        elevation_meters=elevation_meters,
        transform=transform,
        crs=raster_crs,
        nodata=float(nodata) if nodata is not None else None,
        vertical_unit="meter",
        source_path=source_path,
        provenance=provenance,
        cell_size_meters=cell_size_meters,
    )


def _refuse_non_meter_linear_units(crs: CRS) -> None:
    """Projected linear units must be meters so area_m2 and cell sizes stay honest."""
    for axis in crs.axis_info:
        unit = (axis.unit_name or "").lower()
        if "degree" in unit or "radian" in unit:
            continue
        if "foot" in unit or unit in {"ft", "us-ft", "us survey foot"}:
            raise DemValidationError(
                f"CRS axis '{axis.name}' uses {axis.unit_name}; reproject to meters"
            )
        factor = axis.unit_conversion_factor
        if factor is None:
            continue
        if abs(factor - 1.0) > 1e-3:
            raise DemValidationError(
                f"CRS axis '{axis.name}' uses {axis.unit_name}; reproject to meters"
            )


def _observation_kind(tags: dict[str, str]) -> ObservationKind:
    raw = tags.get("TERRASCOUT_OBSERVATION_KIND", "unknown")
    if raw in {"synthetic", "usgs_3dep", "local_user", "unknown"}:
        return raw  # type: ignore[return-value]
    return "unknown"


def _cell_size_meters(
    transform: Affine,
    crs: CRS,
    shape: tuple[int, ...],
) -> tuple[float, float]:
    pixel_width = float(abs(transform.a))
    pixel_height = float(abs(transform.e))
    if crs.is_projected:
        return (pixel_width, pixel_height)
    if not crs.is_geographic:
        raise DemValidationError(f"Unsupported CRS for cell-size conversion: {crs}")
    rows, cols = int(shape[0]), int(shape[1])
    left, bottom, right, top = array_bounds(rows, cols, transform)
    center_lat = (top + bottom) / 2.0
    center_lon = (left + right) / 2.0
    geod = Geod(ellps="WGS84")
    _, _, east_m = geod.inv(center_lon, center_lat, center_lon + pixel_width, center_lat)
    _, _, north_m = geod.inv(center_lon, center_lat, center_lon, center_lat + pixel_height)
    return (abs(east_m), abs(north_m))
