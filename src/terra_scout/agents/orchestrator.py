from __future__ import annotations

from pathlib import Path

from terra_scout.agents.detection import run_detection
from terra_scout.agents.geospatial import inspect_dem
from terra_scout.agents.llm import LanguageModelClient
from terra_scout.agents.reporting import write_report
from terra_scout.agents.research import research_context
from terra_scout.agents.schemas import AgentTrace, SwarmReport, ToolTrace
from terra_scout.agents.skeptic import critique_candidates
from terra_scout.agents.verification import verify_candidates
from terra_scout.io.dem import load_dem
from terra_scout.registry.store import CandidateStore
from terra_scout.terrain.layers import compute_terrain_layers
from terra_scout.viz.export import export_analysis


def run_swarm(
    *,
    dem_path: Path,
    study_area_path: Path | None,
    output_dir: Path,
) -> SwarmReport:
    """Deterministic specialist swarm. LLM is optional and unused by default."""
    del study_area_path  # geometry stays local; not forwarded to external APIs
    output_dir.mkdir(parents=True, exist_ok=True)
    llm = LanguageModelClient()
    llm_was_used = llm.complete("status") is not None
    geospatial_trace = inspect_dem(dem_path)
    dem = load_dem(dem_path)
    detection, detection_trace = run_detection(dem)
    research_trace = research_context(dem)
    critiques = critique_candidates(dem, detection.candidates)
    for candidate, critique in zip(detection.candidates, critiques, strict=False):
        candidate.alternative_explanations = critique.alternative_explanations
    verification_trace = verify_candidates(dem, detection.candidates)
    layers = compute_terrain_layers(dem)
    export_analysis(dem, layers, detection, output_dir / "products")
    store = CandidateStore(output_dir / "registry.sqlite3")
    store.add_candidates(detection.candidates)
    traces = [
        geospatial_trace,
        detection_trace,
        research_trace,
        _skeptic_trace(critiques),
        verification_trace,
    ]
    report = write_report(
        dem=dem,
        candidates=detection.candidates,
        critiques=critiques,
        traces=traces,
        output_dir=output_dir,
        llm_was_used=llm_was_used,
    )
    report.agent_traces = [
        *traces,
        _reporting_trace(report.report_path),
    ]
    return report


def _skeptic_trace(critiques: list) -> AgentTrace:
    return AgentTrace(
        agent_id="skeptic",
        task_id="critique",
        tool_calls=[
            ToolTrace(
                tool_name="critique_candidates",
                output_summary=f"{len(critiques)} critiques",
                succeeded=True,
            )
        ],
        notes=["Alternatives are hypotheses, not proof of a natural origin."],
        candidate_ids=[item.candidate_id for item in critiques],
    )


def _reporting_trace(report_path: Path) -> AgentTrace:
    return AgentTrace(
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
