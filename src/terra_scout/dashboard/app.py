from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import streamlit as st

from terra_scout.dashboard.loader import load_analysis_directory
from terra_scout.dashboard.review import LAYER_LABELS, queue_label, render_layer_with_candidates
from terra_scout.detection.models import ReviewStatus

REVIEW_STATUSES: tuple[ReviewStatus, ...] = (
    "unreviewed",
    "likely_natural",
    "likely_modern",
    "needs_research",
    "potential_anthropogenic_feature",
    "expert_reviewed",
    "rejected",
)

st.set_page_config(
    page_title="TerraScout",
    layout="wide",
    menu_items={
        "Get help": None,
        "Report a bug": None,
        "About": (
            "TerraScout is a local review workstation. "
            "Anomaly detection is not archaeological confirmation."
        ),
    },
)

st.title("TerraScout")
st.caption("Local review workstation for terrain anomalies.")
st.warning(
    "Local-only. Do not publish unpublished candidate coordinates. "
    "Anomaly detection is not archaeological confirmation."
)

default_dir = Path("output/analyze")
analysis_dir = Path(
    st.sidebar.text_input("Analysis directory", value=str(default_dir))
)
state = load_analysis_directory(analysis_dir)

if state.status == "empty":
    st.info(state.message)
    st.stop()
if state.status == "error":
    st.error(state.message)
    st.stop()

st.caption(f"observation_kind: `{state.observation_kind}`")
st.info(state.message)

layer_keys = [name for name in LAYER_LABELS if name in state.layer_paths]
if not layer_keys and "hillshade" in state.layer_paths:
    layer_keys = ["hillshade"]

queue, terrain = st.columns((1, 1.7), gap="large")

selected = state.candidates[0] if state.candidates else None
with queue:
    st.subheader("Queue")
    st.caption("Highest anomaly score first. Score is not P(archaeological).")
    if not state.candidates:
        st.write("No registry candidates in this directory.")
    else:
        labels = [queue_label(item) for item in state.candidates]
        chosen = st.radio("Candidates", labels, label_visibility="collapsed")
        selected = state.candidates[labels.index(chosen)]
        st.subheader("Inspector")
        st.metric("Anomaly score", f"{selected.anomaly_score:.3f}")
        st.caption(selected.anomaly_score_definition)
        st.write(
            f"**{selected.feature_category}** · area {selected.area_m2:.1f} m² · "
            f"circularity {selected.circularity:.2f} · elongation {selected.elongation:.2f}"
        )
        st.write(
            f"Residual contrast {selected.elevation_contrast_m:.2f} m · "
            f"local slope {selected.local_slope_degrees:.1f}°"
        )
        if selected.alternative_explanations:
            st.markdown("**Other explanations (not disproof)**")
            for note in selected.alternative_explanations:
                st.write(f"- {note}")
        choice = st.selectbox(
            "Review status",
            options=list(REVIEW_STATUSES),
            index=list(REVIEW_STATUSES).index(selected.review_status),
            help="expert_reviewed is for a qualified reviewer only. Software cannot assign that.",
        )
        if choice != selected.review_status:
            from terra_scout.registry.store import CandidateStore

            CandidateStore(analysis_dir / "registry.sqlite3").set_review_status(
                selected.candidate_id,
                choice,
            )
            st.rerun()

with terrain:
    st.subheader("Terrain")
    if layer_keys:
        layer_name = st.radio(
            "Layer",
            layer_keys,
            format_func=lambda key: LAYER_LABELS.get(key, key),
            horizontal=True,
        )
        figure = render_layer_with_candidates(
            state.layer_paths[layer_name],
            state.candidates,
            selected.candidate_id if selected else None,
        )
        st.pyplot(figure, width="stretch")
        plt.close(figure)
    elif state.hillshade_png:
        st.image(str(state.hillshade_png), caption="Hillshade preview")

if state.map_path:
    st.subheader("Local map")
    st.caption("Stays on this machine. Do not publish unpublished coordinates.")
    st.iframe(state.map_path, height=420)

if state.report_path:
    with st.expander("Text evidence report"):
        st.text(state.report_path.read_text(encoding="utf-8")[:8000])
