from __future__ import annotations

from terra_scout.agents.schemas import AgentTrace, ToolTrace
from terra_scout.detection.models import CandidateFeature
from terra_scout.io.dem import DigitalElevationModel


def verify_candidates(
    dem: DigitalElevationModel,
    candidates: list[CandidateFeature],
) -> AgentTrace:
    notes = [
        "Absence from OSM or web inventories is not evidence the place is unknown.",
        "Agent agreement is not independent scientific evidence.",
        "Human expert review is required before any discovery claim.",
    ]
    if dem.observation_kind == "synthetic":
        notes.append("Independent-dataset check skipped: raster is a labeled synthetic fixture.")
    elif dem.observation_kind == "usgs_3dep":
        notes.append(
            "Elevation source is USGS 3DEP. A second DEM vintage was not automatically downloaded."
        )
    return AgentTrace(
        agent_id="verification",
        task_id="verify",
        tool_calls=[
            ToolTrace(
                tool_name="independent_dataset_gate",
                arguments={"observation_kind": dem.observation_kind},
                output_summary=f"{len(candidates)} candidates remain unreviewed",
                succeeded=True,
            )
        ],
        notes=notes,
        candidate_ids=[candidate.candidate_id for candidate in candidates],
    )
