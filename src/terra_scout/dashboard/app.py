from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import streamlit as st

from terra_scout.dashboard.copy import (
    ABOUT,
    CAPTION,
    HEADING,
    INSPECTOR_HEADING,
    LOOP_CAPTION,
    PAGE_TITLE,
    QUEUE_CAPTION,
    WARNING,
)
from terra_scout.dashboard.loader import load_analysis_directory
from terra_scout.dashboard.review import (
    LAYER_LABELS,
    evidence_packet,
    queue_label,
    render_layer_with_candidates,
)
from terra_scout.dashboard.theme import CONSOLE_CSS
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
    page_title=PAGE_TITLE,
    layout="wide",
    menu_items={
        "Get help": None,
        "Report a bug": None,
        "About": ABOUT,
    },
)
st.markdown(f"<style>{CONSOLE_CSS}</style>", unsafe_allow_html=True)

st.markdown('<p class="ts-masthead">TERRASCOUT</p>', unsafe_allow_html=True)
st.title(HEADING)
st.caption(CAPTION)
st.caption(LOOP_CAPTION)
st.warning(WARNING)

default_dir = Path("output/analyze")
analysis_dir = Path(
    st.sidebar.text_input("DATA PATH", value=str(default_dir))
)
state = load_analysis_directory(analysis_dir)

if state.status == "empty":
    st.info(state.message)
    st.stop()
if state.status == "error":
    st.error(state.message)
    st.stop()

st.caption(f"OBS.KIND  {state.observation_kind.upper()}  ·  {state.message}")

layer_keys = [name for name in LAYER_LABELS if name in state.layer_paths]
if not layer_keys and "hillshade" in state.layer_paths:
    layer_keys = ["hillshade"]

queue, terrain = st.columns((1, 1.7), gap="large")

selected = state.candidates[0] if state.candidates else None
with queue:
    st.subheader("Queue")
    st.caption(QUEUE_CAPTION)
    if not state.candidates:
        st.write("No registry candidate sites in this directory.")
    else:
        labels = [queue_label(item) for item in state.candidates]
        chosen = st.radio("Candidate sites", labels, label_visibility="collapsed")
        selected = state.candidates[labels.index(chosen)]
        packet = evidence_packet(selected)
        st.subheader(INSPECTOR_HEADING)
        st.metric("ANOMALY SCORE", f"{selected.anomaly_score:.3f}")
        st.caption(str(packet["score_definition"]))
        st.write(f"CLAIM  {packet['claim']}")
        st.write(
            f"NOVELTY  {packet['novelty_status']}  ·  "
            f"{packet['observation_kind']}  ·  {packet['feature_category']}"
        )
        st.caption(str(packet["novelty_note"]))
        st.write(
            f"area {selected.area_m2:.1f} m²  ·  "
            f"circ {selected.circularity:.2f}  ·  elong {selected.elongation:.2f}"
        )
        st.write(
            f"contrast {selected.elevation_contrast_m:.2f} m  ·  "
            f"slope {selected.local_slope_degrees:.1f} deg"
        )
        if selected.alternative_explanations:
            st.markdown("**ALT. EXPLANATIONS (NOT DISPROOF)**")
            for note in selected.alternative_explanations:
                st.write(f"- {note}")
        choice = st.selectbox(
            "REVIEW STATUS",
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
            "CHANNEL",
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
    with st.expander("TELEMETRY LOG"):
        st.text(state.report_path.read_text(encoding="utf-8")[:8000])
