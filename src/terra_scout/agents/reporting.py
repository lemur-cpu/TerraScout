from __future__ import annotations

from pathlib import Path

from terra_scout.agents.schemas import AgentTrace, CandidateCritique, SwarmReport, ToolTrace
from terra_scout.agents.trace_io import write_agent_traces
from terra_scout.detection.models import CandidateFeature
from terra_scout.io.dem import DigitalElevationModel


def write_report(
    *,
    dem: DigitalElevationModel,
    candidates: list[CandidateFeature],
    critiques: list[CandidateCritique],
    traces: list[AgentTrace],
    output_dir: Path,
    llm_was_used: bool,
) -> SwarmReport:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "swarm_report.md"
    by_id = {item.candidate_id: item for item in critiques}
    ranked = sorted(candidates, key=lambda item: item.anomaly_score, reverse=True)
    reporting = AgentTrace(
        agent_id="reporting",
        task_id="write-report",
        tool_calls=[
            ToolTrace(
                tool_name="write_report",
                arguments={"path": str(report_path)},
                output_summary=str(report_path),
                succeeded=True,
            )
        ],
        notes=["Report is for professional review, not public discovery claims."],
    )
    all_traces = [*traces, reporting]
    lines = [
        "# TerraScout swarm report",
        "",
        "Anomaly detection is **not** archaeological confirmation.",
        f"observation_kind: `{dem.observation_kind}`",
        f"llm_was_used: `{llm_was_used}`",
        f"candidates: {len(candidates)}",
        "",
        "## Uncertainties",
        "- Scores are residual statistics, not calibrated site probabilities.",
        "- Modern and natural processes remain plausible for every candidate.",
        "- Do not publish unpublished coordinates.",
        "",
        "## Ranked candidates for professional review",
    ]
    for candidate in ranked[:25]:
        critique = by_id.get(candidate.candidate_id)
        alts = "; ".join(critique.alternative_explanations) if critique else "n/a"
        lines.append(
            f"- `{candidate.candidate_id}` {candidate.feature_category} "
            f"score={candidate.anomaly_score:.2f} alternatives: {alts}"
        )
    lines.extend(["", "## Agent traces"])
    for trace in all_traces:
        lines.append(f"### {trace.agent_id}")
        for note in trace.notes:
            lines.append(f"- {note}")
        for failed in trace.failed_retrievals:
            lines.append(f"- failed retrieval: {failed.source}: {failed.reason}")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    summary = f"{len(candidates)} unreviewed candidates; llm_was_used={llm_was_used}"
    write_agent_traces(
        output_dir / "agent_traces.json",
        summary=summary,
        llm_was_used=llm_was_used,
        candidate_count=len(candidates),
        traces=all_traces,
    )
    return SwarmReport(
        summary=summary,
        report_path=report_path,
        agent_traces=all_traces,
        candidates=candidates,
        llm_was_used=llm_was_used,
        uncertainties=[
            "No calibrated archaeological probability is available.",
            "Human review is required.",
        ],
    )
