from __future__ import annotations

import math
import uuid

import numpy as np
from rasterio import features
from shapely.geometry import shape
from skimage.measure import label, regionprops
from skimage.morphology import disk, opening

from terra_scout.detection.models import (
    ANOMALY_SCORE_DEFINITION,
    CandidateFeature,
    DetectionResult,
    FeatureCategory,
)
from terra_scout.io.dem import DigitalElevationModel
from terra_scout.provenance import ProvenanceRecord
from terra_scout.terrain.derivatives import slope_degrees
from terra_scout.terrain.relief import local_relief_model


def detect_anomalies(
    dem: DigitalElevationModel,
    *,
    z_score_threshold: float = 2.0,
    min_residual_meters: float = 0.35,
    min_pixels: int = 8,
    kernel_radius_pixels: int = 8,
) -> DetectionResult:
    """Conventional residual + morphology detector. Not a trained classifier."""
    relief = local_relief_model(dem, kernel_radius_pixels=kernel_radius_pixels)
    slope = slope_degrees(dem)
    residual = relief.values
    finite = np.isfinite(residual)
    if finite.sum() < 16:
        raise ValueError("DEM has too few finite samples for anomaly detection")

    sample = residual[finite]
    std = float(np.std(sample))
    mean = float(np.mean(sample))
    if std < 1e-6:
        z_scores = np.zeros_like(residual)
    else:
        z_scores = (residual - mean) / std
    z_scores[~finite] = np.nan

    positive = finite & (z_scores >= z_score_threshold) & (residual >= min_residual_meters)
    negative = finite & (z_scores <= -z_score_threshold) & (residual <= -min_residual_meters)
    positive = opening(positive, disk(1))
    negative = opening(negative, disk(1))

    parameters = {
        "z_score_threshold": z_score_threshold,
        "min_residual_meters": min_residual_meters,
        "min_pixels": min_pixels,
        "kernel_radius_pixels": kernel_radius_pixels,
        "method": "lrm-zscore-connected-components",
    }
    candidates: list[CandidateFeature] = []
    candidates.extend(
        _components_to_candidates(
            dem=dem,
            mask=positive,
            residual=residual,
            slope_values=slope.values,
            polarity="positive",
            min_pixels=min_pixels,
            parameters=parameters,
        )
    )
    candidates.extend(
        _components_to_candidates(
            dem=dem,
            mask=negative,
            residual=residual,
            slope_values=slope.values,
            polarity="negative",
            min_pixels=min_pixels,
            parameters=parameters,
        )
    )
    provenance = ProvenanceRecord(
        source_path=dem.source_path,
        observation_kind=dem.observation_kind,
        processor="terra-scout.detection.pipeline.detect_anomalies",
        parameters=parameters,
        parent_ids=["dem", "local_relief", "slope_degrees"],
        notes=["anomaly_score is not P(archaeological)"],
    )
    return DetectionResult(
        candidates=candidates,
        layer_names=["local_relief", "slope_degrees"],
        parameters=parameters,
        provenance=provenance,
    )


def _components_to_candidates(
    *,
    dem: DigitalElevationModel,
    mask: np.ndarray,
    residual: np.ndarray,
    slope_values: np.ndarray,
    polarity: str,
    min_pixels: int,
    parameters: dict[str, float | int | str],
) -> list[CandidateFeature]:
    labeled = label(mask, connectivity=2)
    candidates: list[CandidateFeature] = []
    dx, dy = dem.cell_size_meters
    pixel_area = abs(dx * dy)
    for region in regionprops(labeled):
        if region.area < min_pixels:
            continue
        component = labeled == region.label
        shapes = list(
            features.shapes(
                component.astype(np.uint8),
                mask=component,
                transform=dem.transform,
            )
        )
        if not shapes:
            continue
        geom = shape(shapes[0][0])
        if geom.is_empty:
            continue
        perimeter = max(geom.length, 1e-6)
        area_m2 = float(region.area * pixel_area)
        circularity = float(min(1.0, (4.0 * math.pi * geom.area) / (perimeter**2)))
        elongation = _elongation(region)
        mean_residual = float(np.nanmean(residual[component]))
        mean_z = float(mean_residual / (np.nanstd(residual) + 1e-6))
        anomaly_score = abs(mean_z) * max(circularity, 0.05)
        category = _classify(polarity=polarity, circularity=circularity, elongation=elongation)
        candidates.append(
            CandidateFeature(
                candidate_id=str(uuid.uuid4()),
                feature_category=category,
                geometry_wkt=geom.wkt,
                crs_epsg=dem.crs.to_epsg(),
                area_m2=area_m2,
                perimeter_m=float(perimeter),
                circularity=circularity,
                elongation=elongation,
                orientation_degrees=float(np.degrees(region.orientation)),
                elevation_contrast_m=mean_residual,
                local_slope_degrees=float(np.nanmean(slope_values[component])),
                anomaly_score=float(anomaly_score),
                anomaly_score_definition=ANOMALY_SCORE_DEFINITION,
                detection_method="lrm-zscore-connected-components",
                data_quality={
                    "valid_fraction": dem.valid_fraction,
                    "pixel_count": int(region.area),
                    "polarity": polarity,
                },
                observation_kind=dem.observation_kind,
                provenance=ProvenanceRecord(
                    source_path=dem.source_path,
                    observation_kind=dem.observation_kind,
                    processor="terra-scout.detection.pipeline",
                    parameters=dict(parameters),
                    parent_ids=["dem"],
                ),
            )
        )
    return candidates


def _elongation(region: object) -> float:
    minor = float(getattr(region, "axis_minor_length", 0.0) or 0.0)
    major = float(getattr(region, "axis_major_length", 0.0) or 0.0)
    if minor <= 1e-6:
        return 99.0 if major > 0 else 1.0
    return major / minor


def _classify(*, polarity: str, circularity: float, elongation: float) -> FeatureCategory:
    if polarity == "negative":
        return "ditch_or_depression"
    if elongation >= 3.5:
        return "linear_embankment"
    if circularity >= 0.55 and elongation < 2.2:
        return "mound_like"
    if circularity < 0.35 and elongation < 2.5:
        return "platform_or_terrace"
    return "unknown_anomaly"
