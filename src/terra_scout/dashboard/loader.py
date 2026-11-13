from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DashboardState:
    status: str
    message: str
    candidate_count: int = 0
    hillshade_png: Path | None = None
    geojson_path: Path | None = None
    report_path: Path | None = None


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
    count = 0
    if geojson.exists():
        payload = json.loads(geojson.read_text(encoding="utf-8"))
        count = len(payload.get("features") or [])
    report = path / "report.txt"
    swarm = path / "swarm_report.md"
    report_path = swarm if swarm.exists() else (report if report.exists() else None)
    return DashboardState(
        status="ok",
        message=f"{count} unreviewed candidates. Not archaeological confirmation.",
        candidate_count=count,
        hillshade_png=preview if preview.exists() else None,
        geojson_path=geojson if geojson.exists() else None,
        report_path=report_path,
    )
