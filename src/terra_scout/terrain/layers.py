from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from terra_scout.io.dem import DigitalElevationModel
from terra_scout.provenance import ProvenanceRecord


@dataclass(frozen=True)
class TerrainLayer:
    name: str
    values: NDArray[np.float64]
    source_dem: DigitalElevationModel
    provenance: ProvenanceRecord

    def __getitem__(self, key: Any) -> Any:
        return self.values[key]

    def __array__(self, dtype: Any = None) -> np.ndarray:
        if dtype is None:
            return self.values
        return self.values.astype(dtype)


def compute_terrain_layers(dem: DigitalElevationModel) -> dict[str, TerrainLayer]:
    from terra_scout.terrain.derivatives import curvature, slope_degrees, terrain_ruggedness_index
    from terra_scout.terrain.relief import (
        local_relief_model,
        multidirectional_hillshade,
        multiscale_tpi,
        sky_view_factor,
    )

    return {
        "hillshade": multidirectional_hillshade(dem),
        "slope_degrees": slope_degrees(dem),
        "curvature": curvature(dem),
        "local_relief": local_relief_model(dem),
        "tpi": multiscale_tpi(dem),
        "sky_view_factor": sky_view_factor(dem),
        "ruggedness": terrain_ruggedness_index(dem),
    }
