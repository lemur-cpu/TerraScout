from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from terra_scout.analyze import analyze_dem
from terra_scout.data.usgs import download_3dep_subset
from terra_scout.io.dem import load_dem

# Documented public 3DEP demo box (README). Small, size-capped friendly.
DEMO_BBOX: tuple[float, float, float, float] = (-90.070, 38.655, -90.055, 38.665)


class AcquireError(ValueError):
    """Invalid acquire inputs."""


@dataclass(frozen=True)
class AcquireResult:
    dem_path: Path
    output_dir: Path
    observation_kind: str
    candidate_count: int


def parse_bbox(
    *,
    west: float,
    south: float,
    east: float,
    north: float,
) -> tuple[float, float, float, float]:
    if not (west < east and south < north):
        raise AcquireError("bbox must have west < east and south < north")
    if west < -180 or east > 180 or south < -90 or north > 90:
        raise AcquireError("bbox coordinates must be valid WGS84 degrees")
    return west, south, east, north


def acquire_and_analyze(
    *,
    west: float,
    south: float,
    east: float,
    north: float,
    cache_dir: Path,
    output_dir: Path,
    max_megabytes: float,
) -> AcquireResult:
    """Download a size-capped 3DEP subset and run conventional DEM analysis."""
    west, south, east, north = parse_bbox(
        west=west, south=south, east=east, north=north
    )
    dem_path = download_3dep_subset(
        west,
        south,
        east,
        north,
        output_dir=cache_dir,
        max_megabytes=max_megabytes,
    )
    dem = load_dem(dem_path)
    written = analyze_dem(dem_path, output_dir)
    from terra_scout.registry.store import CandidateStore

    count = len(CandidateStore(written["registry"]).list_candidates())
    return AcquireResult(
        dem_path=dem_path,
        output_dir=output_dir,
        observation_kind=dem.observation_kind,
        candidate_count=count,
    )
