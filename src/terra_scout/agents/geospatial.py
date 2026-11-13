from __future__ import annotations

from pathlib import Path

from terra_scout.agents.schemas import AgentTrace, ToolTrace
from terra_scout.io.dem import load_dem


def inspect_dem(dem_path: Path) -> AgentTrace:
    dem = load_dem(dem_path)
    summary = (
        f"crs={dem.crs.to_string()} shape={dem.elevation_meters.shape} "
        f"valid_fraction={dem.valid_fraction:.3f} "
        f"cell_m={dem.cell_size_meters} kind={dem.observation_kind}"
    )
    notes = [
        "DEM-only workflow; PDAL was not required.",
        "Empty USGS searches remain valid: coverage is not universal.",
    ]
    if dem.valid_fraction < 0.8:
        notes.append("Low valid-pixel fraction; treat detections as data-quality limited.")
    return AgentTrace(
        agent_id="geospatial",
        task_id="inspect-dem",
        tool_calls=[
            ToolTrace(
                tool_name="load_dem",
                arguments={"path": str(dem_path)},
                output_summary=summary,
                succeeded=True,
            )
        ],
        notes=notes,
    )
