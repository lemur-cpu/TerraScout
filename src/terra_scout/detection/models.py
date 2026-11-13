from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from terra_scout.provenance import ObservationKind, ProvenanceRecord

FeatureCategory = Literal[
    "mound_like",
    "circular_earthwork",
    "rectangular_earthwork",
    "linear_embankment",
    "ditch_or_depression",
    "platform_or_terrace",
    "geometric_alignment",
    "unknown_anomaly",
]

ReviewStatus = Literal[
    "unreviewed",
    "likely_natural",
    "likely_modern",
    "needs_research",
    "potential_anthropogenic_feature",
    "expert_reviewed",
    "rejected",
]

ANOMALY_SCORE_DEFINITION = (
    "residual z-score of the local relief model multiplied by compactness "
    "(4*pi*area/perimeter^2). This is a dimensionless anomaly statistic, "
    "not a calibrated archaeological probability."
)

NoveltyStatus = Literal["not_demonstrated", "synthetic_na"]

NOVELTY_NOTE_NOT_DEMONSTRATED = (
    "Literature was not retrieved. Novelty is not demonstrated. "
    "A missing record is not proof the place is unknown."
)
NOVELTY_NOTE_SYNTHETIC = "Synthetic fixture. Novelty does not apply."


def novelty_for(observation_kind: ObservationKind) -> tuple[NoveltyStatus, str]:
    if observation_kind == "synthetic":
        return "synthetic_na", NOVELTY_NOTE_SYNTHETIC
    return "not_demonstrated", NOVELTY_NOTE_NOT_DEMONSTRATED


class CandidateFeature(BaseModel):
    candidate_id: str
    feature_category: FeatureCategory
    geometry_wkt: str
    crs_epsg: int | None
    area_m2: float
    perimeter_m: float
    circularity: float
    elongation: float
    orientation_degrees: float
    elevation_contrast_m: float
    local_slope_degrees: float
    anomaly_score: float
    anomaly_score_definition: str = ANOMALY_SCORE_DEFINITION
    detection_method: str
    data_quality: dict[str, Any] = Field(default_factory=dict)
    review_status: ReviewStatus = "unreviewed"
    observation_kind: ObservationKind
    novelty_status: NoveltyStatus = "not_demonstrated"
    novelty_note: str = NOVELTY_NOTE_NOT_DEMONSTRATED
    provenance: ProvenanceRecord
    alternative_explanations: list[str] = Field(default_factory=list)
    supporting_evidence: list[str] = Field(default_factory=list)
    contradicting_evidence: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def default_novelty_from_observation_kind(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        kind = data.get("observation_kind", "unknown")
        status, note = novelty_for(kind)
        data.setdefault("novelty_status", status)
        data.setdefault("novelty_note", note)
        return data


class DetectionResult(BaseModel):
    candidates: list[CandidateFeature]
    layer_names: list[str]
    parameters: dict[str, Any]
    provenance: ProvenanceRecord
