from __future__ import annotations

from pathlib import Path

from terra_scout.detection.pipeline import detect_anomalies
from terra_scout.io.dem import load_dem
from terra_scout.registry.store import CandidateStore
from terra_scout.terrain.layers import compute_terrain_layers
from terra_scout.viz.export import export_analysis


def analyze_dem(dem_path: Path, output_dir: Path) -> dict[str, Path]:
    dem = load_dem(dem_path)
    layers = compute_terrain_layers(dem)
    detection = detect_anomalies(dem)
    written = export_analysis(dem, layers, detection, output_dir)
    registry_path = output_dir / "registry.sqlite3"
    CandidateStore(registry_path).add_candidates(detection.candidates)
    written["registry"] = registry_path
    return written
