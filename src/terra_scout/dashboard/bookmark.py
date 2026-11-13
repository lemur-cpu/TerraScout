from __future__ import annotations

import math
import uuid

from shapely.geometry import Point

from terra_scout.detection.models import CandidateFeature
from terra_scout.io.dem import DigitalElevationModel
from terra_scout.provenance import ProvenanceRecord

BOOKMARK_BUFFER_M = 25.0
BOOKMARK_SCORE_DEFINITION = (
    "Human nomination from Explore. anomaly_score is 0 and is not a residual "
    "statistic or archaeological probability."
)


def bookmark_candidate(
    *,
    easting: float,
    northing: float,
    dem: DigitalElevationModel,
    buffer_m: float = BOOKMARK_BUFFER_M,
) -> CandidateFeature:
    polygon = Point(easting, northing).buffer(buffer_m)
    area_m2 = float(polygon.area)
    perimeter_m = float(polygon.length)
    circularity = 0.0
    if perimeter_m > 0:
        circularity = float((4.0 * math.pi * area_m2) / (perimeter_m * perimeter_m))
    epsg = dem.crs.to_epsg() if dem.crs is not None else None
    return CandidateFeature(
        candidate_id=f"bookmark-{uuid.uuid4().hex[:12]}",
        feature_category="unknown_anomaly",
        geometry_wkt=polygon.wkt,
        crs_epsg=epsg,
        area_m2=area_m2,
        perimeter_m=perimeter_m,
        circularity=circularity,
        elongation=1.0,
        orientation_degrees=0.0,
        elevation_contrast_m=0.0,
        local_slope_degrees=0.0,
        anomaly_score=0.0,
        anomaly_score_definition=BOOKMARK_SCORE_DEFINITION,
        detection_method="human_bookmark",
        observation_kind=dem.observation_kind,
        provenance=ProvenanceRecord(
            source_path=dem.source_path,
            observation_kind=dem.observation_kind,
            notes=["human_bookmark from Explore"],
        ),
    )
