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

INVENTORY_KEYS = (
    "layers",
    "registry",
    "map",
    "hillshade_png",
    "run_manifest",
    "agent_traces",
    "swarm_report",
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
    product_root: Path | None = None
    layout_kind: str = "unknown"
    inventory: dict[str, bool] = field(default_factory=dict)
    next_unreviewed_id: str | None = None
    run_root: Path | None = None


def queue_message(status_counts: dict[str, int], total: int) -> str:
    unreviewed = status_counts.get("unreviewed", 0)
    return (
        f"{unreviewed} unreviewed of {total} candidate sites. "
        "Not archaeological confirmation."
    )


def resolve_product_root(run_root: Path) -> tuple[Path, str]:
    """Return (product_root, layout_kind) for analyze vs agents layouts."""
    root_registry = run_root / "registry.sqlite3"
    root_geojson = run_root / "candidates.geojson"
    root_preview = run_root / "preview_hillshade.png"
    products = run_root / "products"
    if root_registry.exists() or root_geojson.exists() or root_preview.exists():
        return run_root, "analyze"
    if (products / "registry.sqlite3").exists() or (products / "candidates.geojson").exists():
        return products, "agents"
    if (products / "preview_hillshade.png").exists() or (products / "layers").is_dir():
        return products, "agents"
    return run_root, "analyze"


def _layer_paths(product_root: Path) -> dict[str, Path]:
    return {
        name: layer
        for name in LAYER_FILES
        if (layer := product_root / "layers" / f"{name}.tif").exists()
    }


def _build_inventory(run_root: Path, product_root: Path) -> dict[str, bool]:
    layers = _layer_paths(product_root)
    return {
        "layers": bool(layers),
        "registry": (product_root / "registry.sqlite3").exists(),
        "map": (product_root / "map.html").exists(),
        "hillshade_png": (product_root / "preview_hillshade.png").exists(),
        "run_manifest": (run_root / "run_manifest.json").exists(),
        "agent_traces": (run_root / "agent_traces.json").exists(),
        "swarm_report": (run_root / "swarm_report.md").exists(),
    }


def _next_unreviewed_id(candidates: list[CandidateFeature]) -> str | None:
    for candidate in candidates:
        if candidate.review_status == "unreviewed":
            return candidate.candidate_id
    return None


def load_analysis_directory(path: Path) -> DashboardState:
    if not path.exists():
        return DashboardState(status="error", message="Analysis directory does not exist.")

    product_root, layout_kind = resolve_product_root(path)
    geojson = product_root / "candidates.geojson"
    preview = product_root / "preview_hillshade.png"
    inventory = _build_inventory(path, product_root)

    if not geojson.exists() and not preview.exists() and not inventory["registry"]:
        # Agents root may only have swarm text with no products yet.
        if layout_kind == "agents" and not any(
            inventory[key] for key in ("registry", "layers", "map", "hillshade_png")
        ):
            return DashboardState(
                status="empty",
                message="No analysis products yet. Run `terra-scout analyze --dem ...`.",
                run_root=path,
                product_root=product_root,
                layout_kind=layout_kind,
                inventory=inventory,
            )
        if layout_kind == "analyze":
            return DashboardState(
                status="empty",
                message="No analysis products yet. Run `terra-scout analyze --dem ...`.",
                run_root=path,
                product_root=product_root,
                layout_kind=layout_kind,
                inventory=inventory,
            )

    layer_paths = _layer_paths(product_root)
    map_path = product_root / "map.html"
    report = product_root / "report.txt"
    swarm = path / "swarm_report.md"
    report_path = swarm if swarm.exists() else (report if report.exists() else None)

    candidates: list[CandidateFeature] = []
    registry = product_root / "registry.sqlite3"
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

    if count == 0 and not preview.exists() and not layer_paths and not geojson.exists():
        return DashboardState(
            status="empty",
            message="No analysis products yet. Run `terra-scout analyze --dem ...`.",
            run_root=path,
            product_root=product_root,
            layout_kind=layout_kind,
            inventory=inventory,
        )

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
        product_root=product_root,
        layout_kind=layout_kind,
        inventory=inventory,
        next_unreviewed_id=_next_unreviewed_id(candidates),
        run_root=path,
    )
