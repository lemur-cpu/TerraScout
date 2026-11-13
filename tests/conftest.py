from __future__ import annotations

from pathlib import Path

import pytest

from terra_scout.eval.fixtures import write_synthetic_dem


@pytest.fixture
def synthetic_dem_path(tmp_path: Path) -> Path:
    return write_synthetic_dem(tmp_path / "synthetic_mound.tif")
