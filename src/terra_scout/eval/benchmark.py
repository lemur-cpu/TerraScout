from __future__ import annotations

import json
import time
from pathlib import Path

import yaml
from shapely import wkt
from shapely.geometry import shape

from terra_scout.agents.orchestrator import run_swarm
from terra_scout.detection.pipeline import detect_anomalies
from terra_scout.eval.synthetic import build_synthetic_case
from terra_scout.io.dem import load_dem


def run_benchmark(config_path: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    config = {"name": "synthetic-mound", "observation_kind": "synthetic"}
    if config_path.exists():
        loaded = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        config.update(loaded)
    dem_path, truth = build_synthetic_case(output_dir / "fixture")
    dem = load_dem(dem_path)
    truth_geom = shape(truth["features"][0]["geometry"])

    approaches: dict[str, dict] = {}
    started = time.perf_counter()
    conventional = detect_anomalies(dem)
    approaches["conventional"] = _score(conventional.candidates, truth_geom)
    approaches["conventional"]["seconds"] = time.perf_counter() - started

    started = time.perf_counter()
    single = detect_anomalies(dem)
    approaches["single_agent"] = _score(single.candidates, truth_geom)
    approaches["single_agent"]["seconds"] = time.perf_counter() - started
    approaches["single_agent"]["note"] = (
        "Single-agent path uses the same detector tools without skeptic/verification."
    )

    started = time.perf_counter()
    swarm = run_swarm(dem_path=dem_path, study_area_path=None, output_dir=output_dir / "swarm")
    approaches["swarm"] = _score(swarm.candidates, truth_geom)
    approaches["swarm"]["seconds"] = time.perf_counter() - started
    approaches["swarm"]["skeptic_critiques"] = sum(
        1 for candidate in swarm.candidates if candidate.alternative_explanations
    )

    payload = {
        "name": config.get("name"),
        "observation_kind": "synthetic",
        "spatial_leakage": "none_synthetic_fixture",
        "approaches": approaches,
        "disclaimer": "Synthetic scores are not field accuracy. Live USGS clips are unlabeled.",
    }
    result_path = output_dir / "benchmark.json"
    result_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return result_path


def _score(candidates, truth_geom) -> dict:
    hits = 0
    for candidate in candidates:
        geom = wkt.loads(candidate.geometry_wkt)
        if geom.intersects(truth_geom) and candidate.feature_category == "mound_like":
            hits += 1
    predicted = max(len(candidates), 0)
    precision = hits / predicted if predicted else 0.0
    recall = 1.0 if hits else 0.0
    return {
        "true_positives": hits,
        "predicted": predicted,
        "precision": precision,
        "recall": recall,
        "false_positive_rate": 1.0 - precision,
    }
