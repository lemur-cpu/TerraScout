from __future__ import annotations

import math

from terra_scout.dashboard.acquire import DEMO_BBOX

CONUS_WEST = -125.0
CONUS_EAST = -66.5
CONUS_SOUTH = 24.5
CONUS_NORTH = 49.5
CELL_WIDTH = 0.015
CELL_HEIGHT = 0.010

_TILE_COLS = math.ceil((CONUS_EAST - CONUS_WEST) / CELL_WIDTH)
_TILE_ROWS = math.ceil((CONUS_NORTH - CONUS_SOUTH) / CELL_HEIGHT)


def total_cell_count() -> int:
    return _TILE_COLS * _TILE_ROWS


def _clamp_row(row: int) -> int:
    return max(0, min(_TILE_ROWS - 1, row))


def _clamp_col(col: int) -> int:
    return max(0, min(_TILE_COLS - 1, col))


def make_tile_id(row: int, col: int) -> str:
    row = _clamp_row(row)
    col = _clamp_col(col)
    return f"r{row:04d}c{col:05d}"


def parse_tile_id(tile_id: str) -> tuple[int, int]:
    if len(tile_id) < 10 or tile_id[0] != "r" or "c" not in tile_id:
        raise ValueError(f"invalid tile_id: {tile_id}")
    row_part, col_part = tile_id[1:].split("c", 1)
    return int(row_part), int(col_part)


def tile_bbox(row: int, col: int) -> tuple[float, float, float, float]:
    row = _clamp_row(row)
    col = _clamp_col(col)
    west = CONUS_WEST + col * CELL_WIDTH
    south = CONUS_SOUTH + row * CELL_HEIGHT
    east = min(west + CELL_WIDTH, CONUS_EAST)
    north = min(south + CELL_HEIGHT, CONUS_NORTH)
    return west, south, east, north


def tile_bbox_for_id(tile_id: str) -> tuple[float, float, float, float]:
    row, col = parse_tile_id(tile_id)
    return tile_bbox(row, col)


def tiles_intersecting(
    west: float,
    south: float,
    east: float,
    north: float,
) -> list[str]:
    if not (west < east and south < north):
        raise ValueError("bbox must have west < east and south < north")
    col_min = max(0, math.floor((west - CONUS_WEST) / CELL_WIDTH))
    col_max = min(_TILE_COLS - 1, math.floor((east - CONUS_WEST - 1e-12) / CELL_WIDTH))
    row_min = max(0, math.floor((south - CONUS_SOUTH) / CELL_HEIGHT))
    row_max = min(_TILE_ROWS - 1, math.floor((north - CONUS_SOUTH - 1e-12) / CELL_HEIGHT))
    if col_min > col_max or row_min > row_max:
        return []
    ids: list[str] = []
    for row in range(row_min, row_max + 1):
        for col in range(col_min, col_max + 1):
            ids.append(make_tile_id(row, col))
    return ids


def demo_seed_tiles() -> list[str]:
    west, south, east, north = DEMO_BBOX
    return tiles_intersecting(west, south, east, north)