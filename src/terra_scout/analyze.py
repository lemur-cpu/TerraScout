from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from terra_scout.detection.models import DetectionResult
from terra_scout.detection.pipeline import detect_anomalies
from terra_scout.io.dem import DigitalElevationModel, load_dem
from terra_scout.registry.store import CandidateStore
from terra_scout.terrain.layers import TerrainLayer, compute_terrain_layers
from terra_scout.viz.export import export_analysis


@dataclass(frozen=True)
class AnalysisProducts:
    dem: DigitalElevationModel
    layers: dict[str, TerrainLayer]
    detection: DetectionResult
    written: dict[str, Path]


def run_analysis(dem: DigitalElevationModel) -> tuple[dict[str, TerrainLayer], DetectionResult]:
    layers = compute_terrain_layers(dem)
    detection = detect_anomalies(dem)
    return layers, detection


def persist_analysis(
    dem: DigitalElevationModel,
    layers: dict[str, TerrainLayer],
    detection: DetectionResult,
    output_dir: Path,
) -> dict[str, Path]:
    written = export_analysis(dem, layers, detection, output_dir)
    registry_path = output_dir / "registry.sqlite3"
    CandidateStore(registry_path).add_candidates(detection.candidates)
    written["registry"] = registry_path
    return written


def analyze_loaded_dem(dem: DigitalElevationModel, output_dir: Path) -> AnalysisProducts:
    layers, detection = run_analysis(dem)
    written = persist_analysis(dem, layers, detection, output_dir)
    from terra_scout.dashboard.manifest import write_run_manifest

    if dem.source_path is not None:
        written["run_manifest"] = write_run_manifest(
            output_dir,
            dem_path=dem.source_path,
            observation_kind=dem.observation_kind,
        )
    return AnalysisProducts(dem=dem, layers=layers, detection=detection, written=written)


def analyze_dem(dem_path: Path, output_dir: Path) -> dict[str, Path]:
    dem = load_dem(dem_path)
    return analyze_loaded_dem(dem, output_dir).written
