from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from shapely import wkt

from terra_scout.detection.models import DetectionResult
from terra_scout.io.dem import DigitalElevationModel
from terra_scout.io.geotiff import write_layer_geotiff
from terra_scout.terrain.layers import TerrainLayer


def export_analysis(
    dem: DigitalElevationModel,
    layers: dict[str, TerrainLayer],
    detection: DetectionResult,
    output_dir: Path,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    layer_dir = output_dir / "layers"
    written: dict[str, Path] = {}
    for name, layer in layers.items():
        written[name] = write_layer_geotiff(layer, layer_dir / f"{name}.tif")
    written["preview"] = _write_preview(layers["hillshade"], output_dir / "preview_hillshade.png")
    written["geojson"] = _write_geojson(dem, detection, output_dir / "candidates.geojson")
    written["map"] = _write_html_map(dem, layers["hillshade"], detection, output_dir / "map.html")
    written["report"] = _write_text_report(dem, detection, output_dir / "report.txt")
    return written


def _write_preview(layer: TerrainLayer, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    values = layer.values
    finite = values[np.isfinite(values)]
    vmin, vmax = (float(np.min(finite)), float(np.max(finite))) if finite.size else (0.0, 1.0)
    fig, axis = plt.subplots(figsize=(6, 6))
    axis.imshow(values, cmap="gray", vmin=vmin, vmax=vmax)
    axis.set_title("Multidirectional hillshade (synthetic and USGS clips stay labeled)")
    axis.axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def _write_geojson(
    dem: DigitalElevationModel,
    detection: DetectionResult,
    path: Path,
) -> Path:
    features = []
    for candidate in detection.candidates:
        geom = wkt.loads(candidate.geometry_wkt)
        features.append(
            {
                "type": "Feature",
                "geometry": json.loads(json.dumps(geom.__geo_interface__)),
                "properties": {
                    "candidate_id": candidate.candidate_id,
                    "feature_category": candidate.feature_category,
                    "anomaly_score": candidate.anomaly_score,
                    "anomaly_score_definition": candidate.anomaly_score_definition,
                    "elevation_contrast_m": candidate.elevation_contrast_m,
                    "area_m2": candidate.area_m2,
                    "circularity": candidate.circularity,
                    "elongation": candidate.elongation,
                    "detection_method": candidate.detection_method,
                    "review_status": candidate.review_status,
                    "observation_kind": candidate.observation_kind,
                    "novelty_status": candidate.novelty_status,
                },
            }
        )
    payload = {
        "type": "FeatureCollection",
        "name": "terra_scout_candidates",
        "crs": {"type": "name", "properties": {"name": dem.crs.to_string()}},
        "features": features,
        "disclaimer": (
            "Candidates are terrain anomalies, not confirmed archaeological sites. "
            "Keep unpublished coordinates local. "
            "novelty_status=not_demonstrated means literature was not retrieved."
        ),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _write_html_map(
    dem: DigitalElevationModel,
    hillshade: TerrainLayer,
    detection: DetectionResult,
    path: Path,
) -> Path:
    import folium
    from pyproj import Transformer

    transformer = Transformer.from_crs(dem.crs, "EPSG:4326", always_xy=True)
    left, bottom, right, top = dem.bounds
    west, south = transformer.transform(left, bottom)
    east, north = transformer.transform(right, top)
    center_lat = (south + north) / 2.0
    center_lon = (west + east) / 2.0
    fmap = folium.Map(location=[center_lat, center_lon], zoom_start=16, control_scale=True)
    folium.Rectangle(
        bounds=[[south, west], [north, east]],
        color="#3388ff",
        fill=False,
        tooltip="Study area (local map — do not publish unpublished coordinates)",
    ).add_to(fmap)
    for candidate in detection.candidates:
        geom = wkt.loads(candidate.geometry_wkt)
        lon, lat = transformer.transform(geom.centroid.x, geom.centroid.y)
        folium.CircleMarker(
            location=[lat, lon],
            radius=6,
            color="#c0392b",
            fill=True,
            popup=(
                f"{candidate.feature_category}<br>"
                f"score={candidate.anomaly_score:.2f}<br>"
                f"{candidate.anomaly_score_definition}"
            ),
        ).add_to(fmap)
    path.write_text(fmap.get_root().render(), encoding="utf-8")
    return path


def _write_text_report(
    dem: DigitalElevationModel,
    detection: DetectionResult,
    path: Path,
) -> Path:
    lines = [
        "TerraScout analysis report",
        f"observation_kind={dem.observation_kind}",
        f"source={dem.source_path}",
        f"candidates={len(detection.candidates)}",
        "Anomaly detection is not archaeological confirmation.",
    ]
    for candidate in detection.candidates:
        lines.append(
            f"- {candidate.candidate_id} {candidate.feature_category} "
            f"score={candidate.anomaly_score:.3f} area_m2={candidate.area_m2:.1f}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
