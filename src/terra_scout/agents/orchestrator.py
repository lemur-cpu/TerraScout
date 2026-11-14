from __future__ import annotations

from pathlib import Path

from terra_scout.agents.detection import trace_detection
from terra_scout.agents.geospatial import inspect_dem
from terra_scout.agents.llm import LanguageModelClient
from terra_scout.agents.reporting import write_report
from terra_scout.agents.research import research_context
from terra_scout.agents.schemas import AgentTrace, SwarmReport, ToolTrace
from terra_scout.agents.skeptic import critique_candidates
from terra_scout.agents.verification import verify_candidates
from terra_scout.analyze import persist_analysis, run_analysis
from terra_scout.io.dem import load_dem


def run_swarm(
    *,
    dem_path: Path,
    study_area_path: Path | None,
    output_dir: Path,
    place_name: str | None = None,
) -> SwarmReport:
    """Deterministic specialist swarm. LLM is optional and unused by default."""
    del study_area_path  # geometry stays local; not forwarded to external APIs
    output_dir.mkdir(parents=True, exist_ok=True)
    llm = LanguageModelClient()
    llm_was_used = llm.complete("status") is not None
    dem = load_dem(dem_path)
    geospatial_trace = inspect_dem(dem)
    layers, detection = run_analysis(dem)
    detection_trace = trace_detection(detection)
    research_trace = research_context(dem, place_name=place_name)
    critiques = critique_candidates(dem, detection.candidates)
    for candidate, critique in zip(detection.candidates, critiques, strict=False):
        candidate.alternative_explanations = critique.alternative_explanations
    verification_trace = verify_candidates(dem, detection.candidates)
    persist_analysis(dem, layers, detection, output_dir / "products")
    from terra_scout.dashboard.manifest import write_run_manifest

    write_run_manifest(
        output_dir,
        dem_path=dem_path,
        observation_kind=dem.observation_kind,
    )
    traces = [
        geospatial_trace,
        detection_trace,
        research_trace,
        _skeptic_trace(critiques),
        verification_trace,
    ]
    return write_report(
        dem=dem,
        candidates=detection.candidates,
        traces=traces,
        critiques=critiques,
        output_dir=output_dir,
        llm_was_used=llm_was_used,
    )


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
