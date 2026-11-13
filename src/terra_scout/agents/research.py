from __future__ import annotations

from terra_scout.agents.schemas import AgentTrace, FailedRetrieval, ToolTrace
from terra_scout.ethics import redact_coordinates
from terra_scout.io.dem import DigitalElevationModel

_NOVELTY_FAIL_CLOSED = (
    "Novelty is not demonstrated. "
    "A web miss must never be treated as an undocumented site."
)


def research_context(
    dem: DigitalElevationModel,
    place_name: str | None = None,
) -> AgentTrace:
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

    coarse = redact_coordinates(place_name.strip()) if place_name and place_name.strip() else None
    if not coarse:
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
            failed_retrievals=[
                FailedRetrieval(
                    source="openalex",
                    reason=(
                        "Operator must supply a coarse place name for literature search. "
                        "Precise coordinates were not sent to external scholarly APIs."
                    ),
                )
            ],
            notes=[
                "Insufficient evidence for a site-specific literature summary.",
                _NOVELTY_FAIL_CLOSED,
            ],
        )

    return AgentTrace(
        agent_id="research",
        task_id="literature",
        tool_calls=[
            ToolTrace(
                tool_name="openalex_not_wired",
                arguments={"place_name": coarse},
                output_summary=(
                    f"coarse place name {coarse!r}; OpenAlex not wired; no citations invented"
                ),
                succeeded=True,
            )
        ],
        failed_retrievals=[
            FailedRetrieval(
                source="openalex",
                reason="OpenAlex client is not wired; no citations invented.",
            )
        ],
        notes=[
            f"Coarse place name recorded: {coarse}.",
            "OpenAlex is not wired. No citations invented.",
            _NOVELTY_FAIL_CLOSED,
        ],
    )
