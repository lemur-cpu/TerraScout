from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from terra_scout.detection.models import CandidateFeature
from terra_scout.registry.store import CandidateStore

LAYER_FILES = (
    "hillshade",
    "slope_degrees",
    "local_relief",
    "tpi",
    "curvature",
    "sky_view_factor",
    "ruggedness",
)


@dataclass(frozen=True)
class DashboardState:
    status: str
    message: str
    candidate_count: int = 0
    hillshade_png: Path | None = None
    geojson_path: Path | None = None
    report_path: Path | None = None
    map_path: Path | None = None
    layer_paths: dict[str, Path] = field(default_factory=dict)
    candidates: list[CandidateFeature] = field(default_factory=list)
    observation_kind: str = "unknown"
    status_counts: dict[str, int] = field(default_factory=dict)


def queue_message(status_counts: dict[str, int], total: int) -> str:
    unreviewed = status_counts.get("unreviewed", 0)
    return (
        f"{unreviewed} unreviewed of {total} candidates. "
        "Not archaeological confirmation."
    )


def load_analysis_directory(path: Path) -> DashboardState:
    if not path.exists():
        return DashboardState(status="error", message="Analysis directory does not exist.")
    geojson = path / "candidates.geojson"
    preview = path / "preview_hillshade.png"
    if not geojson.exists() and not preview.exists():
        return DashboardState(
            status="empty",
            message="No analysis products yet. Run `terra-scout analyze --dem ...`.",
        )

    layer_paths = {
        name: layer
        for name in LAYER_FILES
        if (layer := path / "layers" / f"{name}.tif").exists()
    }
    map_path = path / "map.html"
    report = path / "report.txt"
    swarm = path / "swarm_report.md"
    report_path = swarm if swarm.exists() else (report if report.exists() else None)

    candidates: list[CandidateFeature] = []
    registry = path / "registry.sqlite3"
    if registry.exists():
        from terra_scout.dashboard.review import rank_candidates

        candidates = rank_candidates(CandidateStore(registry).list_candidates())
    status_counts = dict(Counter(item.review_status for item in candidates))
    observation_kind = candidates[0].observation_kind if candidates else "unknown"
    count = len(candidates)
    if count == 0 and geojson.exists():
        import json

        payload = json.loads(geojson.read_text(encoding="utf-8"))
        count = len(payload.get("features") or [])
    return DashboardState(
        status="ok",
        message=queue_message(status_counts, count),
        candidate_count=count,
        hillshade_png=preview if preview.exists() else None,
        geojson_path=geojson if geojson.exists() else None,
        report_path=report_path,
        map_path=map_path if map_path.exists() else None,
        layer_paths=layer_paths,
        candidates=candidates,
        observation_kind=observation_kind,
        status_counts=status_counts,
    )
