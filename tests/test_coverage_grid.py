from __future__ import annotations

import math

import pytest

from terra_scout.coverage.grid import (
    CELL_HEIGHT,
    CELL_WIDTH,
    CONUS_EAST,
    CONUS_NORTH,
    CONUS_SOUTH,
    CONUS_WEST,
    demo_seed_tiles,
    make_tile_id,
    parse_tile_id,
    tile_bbox,
    tile_bbox_for_id,
    tiles_intersecting,
    total_cell_count,
)
from terra_scout.dashboard.acquire import DEMO_BBOX


def test_total_cell_count_matches_conus_grid() -> None:
    cols = math.ceil((CONUS_EAST - CONUS_WEST) / CELL_WIDTH)
    rows = math.ceil((CONUS_NORTH - CONUS_SOUTH) / CELL_HEIGHT)
    assert total_cell_count() == cols * rows


def test_tile_id_round_trip_and_bbox_inside_conus() -> None:
    tile_id = make_tile_id(12, 345)
    row, col = parse_tile_id(tile_id)
    assert row == 12 and col == 345
    west, south, east, north = tile_bbox_for_id(tile_id)
    assert west >= CONUS_WEST and south >= CONUS_SOUTH
    assert east <= CONUS_EAST and north <= CONUS_NORTH
    assert west < east and south < north
    assert tile_bbox(row, col) == (west, south, east, north)


def test_demo_seed_tiles_match_demo_bbox() -> None:
    west, south, east, north = DEMO_BBOX
    direct = tiles_intersecting(west, south, east, north)
    assert demo_seed_tiles() == direct
    assert len(direct) >= 1


def test_tiles_intersecting_rejects_inverted_bbox() -> None:
    with pytest.raises(ValueError, match="west < east"):
        tiles_intersecting(-90.0, 38.0, -91.0, 39.0)