from __future__ import annotations

import math

from terra_scout.dashboard.acquire import DEMO_BBOX

CONUS_WEST = -125.0
CONUS_SOUTH = 24.5
CONUS_EAST = -66.5
CONUS_NORTH = 49.5
CELL_LON = 0.015
CELL_LAT = 0.010

_NCOLS = math.ceil((CONUS_EAST - CONUS_WEST) / CELL_LON)
_NROWS = math.ceil((CONUS_NORTH - CONUS_SOUTH) / CELL_LAT)


def total_cell_count() -> int:
    return _NCOLS * _NROWS


def _clamp_ix(ix: int) -> int:
    return max(0, min(_NCOLS - 1, ix))


def _clamp_iy(iy: int) -> int:
    return max(0, min(_NROWS - 1, iy))


def tile_id(ix: int, iy: int) -> str:
    ix = _clamp_ix(ix)
    iy = _clamp_iy(iy)
    return f"c{ix}_r{iy}"


def parse_tile_id(tile_id_str: str) -> tuple[int, int]:
    if "_r" not in tile_id_str or not tile_id_str.startswith("c"):
        raise ValueError(f"invalid tile_id: {tile_id_str}")
    col_part, row_part = tile_id_str.split("_r", 1)
    return int(col_part[1:]), int(row_part)


def tile_bbox(ix: int, iy: int) -> tuple[float, float, float, float]:
    ix = _clamp_ix(ix)
    iy = _clamp_iy(iy)
    west = CONUS_WEST + ix * CELL_LON
    south = CONUS_SOUTH + iy * CELL_LAT
    east = min(west + CELL_LON, CONUS_EAST)
    north = min(south + CELL_LAT, CONUS_NORTH)
    return west, south, east, north


def tile_bbox_for_id(tile_id_str: str) -> tuple[float, float, float, float]:
    ix, iy = parse_tile_id(tile_id_str)
    return tile_bbox(ix, iy)


def tiles_intersecting(
    west: float,
    south: float,
    east: float,
    north: float,
) -> list[str]:
    if not (west < east and south < north):
        raise ValueError("bbox must have west < east and south < north")
    ix_min = max(0, math.floor((west - CONUS_WEST) / CELL_LON))
    ix_max = min(_NCOLS - 1, math.floor((east - CONUS_WEST - 1e-12) / CELL_LON))
    iy_min = max(0, math.floor((south - CONUS_SOUTH) / CELL_LAT))
    iy_max = min(_NROWS - 1, math.floor((north - CONUS_SOUTH - 1e-12) / CELL_LAT))
    if ix_min > ix_max or iy_min > iy_max:
        return []
    ids: list[str] = []
    for iy in range(iy_min, iy_max + 1):
        for ix in range(ix_min, ix_max + 1):
            ids.append(tile_id(ix, iy))
    return ids


def demo_seed_tiles() -> list[str]:
    west, south, east, north = DEMO_BBOX
    return tiles_intersecting(west, south, east, north)