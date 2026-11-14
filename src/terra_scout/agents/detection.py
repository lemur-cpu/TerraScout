from __future__ import annotations

from terra_scout.agents.schemas import AgentTrace, ToolTrace
from terra_scout.detection.models import DetectionResult
from terra_scout.detection.pipeline import detect_anomalies
from terra_scout.io.dem import DigitalElevationModel


def trace_detection(result: DetectionResult) -> AgentTrace:
    return AgentTrace(
        agent_id="detection",
        task_id="detect-anomalies",
        tool_calls=[
            ToolTrace(
                tool_name="detect_anomalies",
                arguments=result.parameters,
                output_summary=f"{len(result.candidates)} candidates",
                succeeded=True,
            )
        ],
        notes=[
            "Conventional LRM z-score detector. Not a trained archaeological model.",
            "anomaly_score is not P(archaeological).",
        ],
        candidate_ids=[candidate.candidate_id for candidate in result.candidates],
    )


def run_detection(dem: DigitalElevationModel) -> tuple[DetectionResult, AgentTrace]:
    result = detect_anomalies(dem)
    return result, trace_detection(result)
