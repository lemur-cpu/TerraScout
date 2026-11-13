from __future__ import annotations

from terra_scout.agents.schemas import CandidateCritique
from terra_scout.detection.models import CandidateFeature
from terra_scout.io.dem import DigitalElevationModel


def critique_candidates(
    dem: DigitalElevationModel,
    candidates: list[CandidateFeature],
) -> list[CandidateCritique]:
    """Challenge each candidate with terrain-derived alternative explanations."""
    critiques: list[CandidateCritique] = []
    for candidate in candidates:
        alternatives: list[str] = []
        if dem.observation_kind == "synthetic":
            alternatives.append("synthetic test fixture rather than a field feature")
        if candidate.elongation >= 3.0:
            alternatives.append("road, field drain, plow line, or pipeline corridor")
        if candidate.local_slope_degrees >= 8.0:
            alternatives.append("natural slope break, terrace remnant, or erosion scarp")
        if abs(candidate.elevation_contrast_m) < 0.5:
            alternatives.append("DEM noise, interpolation ripple, or vegetation residual")
        if candidate.feature_category == "mound_like":
            alternatives.append("natural knoll, spoil pile, or modern landscaping")
        if candidate.feature_category == "ditch_or_depression":
            alternatives.append("stream channel, borrow pit, or lidar swath artifact")
        if not alternatives:
            alternatives.append("unspecified natural or modern process; evidence is inconclusive")
        critiques.append(
            CandidateCritique(
                candidate_id=candidate.candidate_id,
                alternative_explanations=alternatives,
            )
        )
    return critiques
