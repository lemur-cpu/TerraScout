from __future__ import annotations

from terra_scout.agents.schemas import AgentTrace, FailedRetrieval, ToolTrace
from terra_scout.io.dem import DigitalElevationModel


def research_context(dem: DigitalElevationModel) -> AgentTrace:
    """Literature lookup. Never fabricates sources. Skips synthetic fixtures."""
    if dem.observation_kind == "synthetic":
        return AgentTrace(
            agent_id="research",
            task_id="literature",
            tool_calls=[
                ToolTrace(
                    tool_name="skip_literature_for_synthetic",
                    output_summary="synthetic fixture is not a real landscape",
                    succeeded=True,
                )
            ],
            notes=[
                "observation_kind=synthetic; no place-name literature search was run.",
                "A web miss must never be treated as an undocumented site.",
            ],
        )

    failed = [
        FailedRetrieval(
            source="openalex",
            reason=(
                "Precise coordinates were not sent to external scholarly APIs "
                "(TERRASCOUT_SEND_PRECISE_COORDINATES_TO_LLM defaults false). "
                "Operator must supply a coarse place name for literature search."
            ),
        )
    ]
    return AgentTrace(
        agent_id="research",
        task_id="literature",
        tool_calls=[
            ToolTrace(
                tool_name="openalex_deferred",
                output_summary="no coarse place name provided; no citations invented",
                succeeded=True,
            )
        ],
        failed_retrievals=failed,
        notes=["Insufficient evidence for a site-specific literature summary."],
    )
