from __future__ import annotations

import importlib

import matplotlib.pyplot as plt
import streamlit as st

from terra_scout.dashboard import review as _dashboard_review
from terra_scout.dashboard.loader import DashboardState
from terra_scout.dashboard.traces import load_agent_traces
from terra_scout.detection.models import ReviewStatus
from terra_scout.registry.store import CandidateStore

REVIEW_STATUSES: tuple[ReviewStatus, ...] = (
    "unreviewed",
    "likely_natural",
    "likely_modern",
    "needs_research",
    "potential_anthropogenic_feature",
    "expert_reviewed",
    "rejected",
)


def render_investigate(state: DashboardState, copy_mod) -> None:
    review = importlib.reload(_dashboard_review)
    st.subheader(copy_mod.INVESTIGATE_HEADING)
    st.caption(copy_mod.INVESTIGATE_CAPTION)
    st.caption(copy_mod.LOOP_CAPTION)

    if not state.candidates:
        st.write("No registry candidate sites in this directory.")
        return

    labels = [review.queue_label(item) for item in state.candidates]
    ids = [item.candidate_id for item in state.candidates]
    preferred = st.session_state.get("selected_candidate_id")
    index = ids.index(preferred) if preferred in ids else 0
    chosen = st.radio(
        "Candidate sites",
        labels,
        index=index,
        label_visibility="collapsed",
    )
    selected = state.candidates[labels.index(chosen)]
    st.session_state.selected_candidate_id = selected.candidate_id

    packet = review.evidence_packet(selected)
    st.subheader(copy_mod.INSPECTOR_HEADING)
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
    if selected.supporting_evidence:
        st.markdown("**SUPPORTING**")
        for note in selected.supporting_evidence:
            st.write(f"- {note}")
    if selected.contradicting_evidence:
        st.markdown("**CONTRADICTING**")
        for note in selected.contradicting_evidence:
            st.write(f"- {note}")
    if not (
        selected.alternative_explanations
        or selected.supporting_evidence
        or selected.contradicting_evidence
    ):
        st.caption(copy_mod.SKEPTIC_EMPTY)

    st.markdown("**Specialist traces**")
    _render_traces(state, copy_mod)

    choice = st.selectbox(
        "REVIEW STATUS",
        options=list(REVIEW_STATUSES),
        index=list(REVIEW_STATUSES).index(selected.review_status),
        help="expert_reviewed is for a qualified reviewer only. Software cannot assign that.",
    )
    if choice != selected.review_status:
        assert state.product_root is not None
        CandidateStore(state.product_root / "registry.sqlite3").set_review_status(
            selected.candidate_id,
            choice,
        )
        st.rerun()

    layer_keys = [name for name in review.LAYER_LABELS if name in state.layer_paths]
    if layer_keys:
        st.markdown("**Focused terrain**")
        layer_name = st.radio(
            "CHANNEL",
            layer_keys,
            format_func=lambda key: review.LAYER_LABELS.get(key, key),
            horizontal=True,
            key="investigate_layer",
        )
        figure = review.render_layer_with_candidates(
            state.layer_paths[layer_name],
            state.candidates,
            selected.candidate_id,
        )
        st.pyplot(figure, width="stretch")
        plt.close(figure)


def _render_traces(state: DashboardState, copy_mod) -> None:
    if state.run_root is None:
        st.caption(copy_mod.TRACES_EMPTY)
        return
    payload = load_agent_traces(state.run_root / "agent_traces.json")
    if payload is None:
        st.caption(copy_mod.TRACES_EMPTY)
        return
    for trace in payload.get("traces") or []:
        with st.expander(str(trace.get("agent_id", "agent")), expanded=False):
            for note in trace.get("notes") or []:
                st.write(f"- {note}")
            for tool in trace.get("tool_calls") or []:
                mark = "ok" if tool.get("succeeded") else "fail"
                st.write(f"- [{mark}] {tool.get('tool_name')}: {tool.get('output_summary')}")
            for failed in trace.get("failed_retrievals") or []:
                st.write(f"- failed: {failed.get('source')}: {failed.get('reason')}")
