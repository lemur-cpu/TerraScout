from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.figure import Figure
from rasterio.transform import rowcol
from shapely import wkt

from terra_scout.dashboard.theme import PHOSPHOR_AMBER, PHOSPHOR_DIM, TERMINAL_BG
from terra_scout.detection.models import CandidateFeature

LAYER_LABELS = {
    "hillshade": "HILLSHADE",
    "local_relief": "LRM",
    "slope_degrees": "SLOPE",
    "tpi": "TPI",
}


def rank_candidates(candidates: list[CandidateFeature]) -> list[CandidateFeature]:
    return sorted(candidates, key=lambda item: item.anomaly_score, reverse=True)


def evidence_packet(candidate: CandidateFeature) -> dict[str, object]:
    """Inspectable facts for a candidate site. Omits WKT so packets are not a coord dump."""
    return {
        "claim": "candidate site — not a confirmed archaeological site",
        "candidate_id": candidate.candidate_id,
        "feature_category": candidate.feature_category,
        "review_status": candidate.review_status,
        "anomaly_score": candidate.anomaly_score,
        "score_definition": candidate.anomaly_score_definition,
        "observation_kind": candidate.observation_kind,
        "novelty_status": candidate.novelty_status,
        "novelty_note": candidate.novelty_note,
        "area_m2": candidate.area_m2,
        "circularity": candidate.circularity,
        "elongation": candidate.elongation,
        "elevation_contrast_m": candidate.elevation_contrast_m,
        "local_slope_degrees": candidate.local_slope_degrees,
        "alternative_explanations": list(candidate.alternative_explanations),
        "supporting_evidence": list(candidate.supporting_evidence),
        "contradicting_evidence": list(candidate.contradicting_evidence),
        "loop": "scan → rank → evidence packet → human / authority",
    }


def queue_label(candidate: CandidateFeature) -> str:
    return (
        f"> {candidate.feature_category}   "
        f"{candidate.anomaly_score:.2f}   "
        f"{candidate.review_status}"
    )


def render_layer_with_candidates(
    layer_path: Path,
    candidates: list[CandidateFeature],
    selected_id: str | None,
) -> Figure:
    """Draw a relief layer in pixel space with candidate outlines. Local review only."""
    with rasterio.open(layer_path) as dataset:
        values = dataset.read(1)
        transform = dataset.transform
    finite = values[np.isfinite(values)]
    if finite.size:
        vmin = float(np.nanpercentile(finite, 2))
        vmax = float(np.nanpercentile(finite, 98))
        if vmin == vmax:
            vmax = vmin + 1.0
    else:
        vmin, vmax = 0.0, 1.0
    figure, axis = plt.subplots(figsize=(7, 7), facecolor=TERMINAL_BG)
    axis.set_facecolor(TERMINAL_BG)
    axis.imshow(values, cmap="gray", vmin=vmin, vmax=vmax)
    for candidate in candidates:
        geom = wkt.loads(candidate.geometry_wkt)
        if geom.is_empty:
            continue
        poly = geom if geom.geom_type == "Polygon" else geom.convex_hull
        xs, ys = zip(*poly.exterior.coords, strict=True)
        rows, cols = rowcol(transform, xs, ys)
        selected = candidate.candidate_id == selected_id
        axis.plot(
            cols,
            rows,
            color=PHOSPHOR_AMBER if selected else PHOSPHOR_DIM,
            linewidth=2.4 if selected else 1.2,
        )
    axis.set_axis_off()
    axis.set_title(
        "Candidate outline on terrain  ·  score is not site probability",
        color=PHOSPHOR_AMBER,
        fontsize=9,
        fontfamily="monospace",
        loc="left",
        pad=8,
    )
    figure.tight_layout()
    return figure
