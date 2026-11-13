from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.figure import Figure
from rasterio.transform import rowcol
from shapely import wkt

from terra_scout.detection.models import CandidateFeature

LAYER_LABELS = {
    "hillshade": "Hillshade",
    "local_relief": "Local relief",
    "slope_degrees": "Slope",
    "tpi": "TPI",
}


def rank_candidates(candidates: list[CandidateFeature]) -> list[CandidateFeature]:
    return sorted(candidates, key=lambda item: item.anomaly_score, reverse=True)


def queue_label(candidate: CandidateFeature) -> str:
    return (
        f"{candidate.feature_category}  "
        f"score={candidate.anomaly_score:.2f}  "
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
    figure, axis = plt.subplots(figsize=(7, 7))
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
            color="#9B2C2C" if selected else "#C9A227",
            linewidth=2.4 if selected else 1.2,
        )
    axis.set_axis_off()
    axis.set_title("Candidate outlines on terrain. Score is not P(archaeological).")
    figure.tight_layout()
    return figure
