from __future__ import annotations

from pathlib import Path

import streamlit as st

from terra_scout.dashboard.loader import load_analysis_directory

st.set_page_config(page_title="TerraScout", layout="wide")
st.title("TerraScout research dashboard")
st.warning(
    "Local-only. Do not publish unpublished candidate coordinates. "
    "Anomaly detection is not archaeological confirmation."
)

analysis_dir = Path(
    st.sidebar.text_input("Analysis directory", value="output/analyze")
)
state = load_analysis_directory(analysis_dir)

if state.status == "empty":
    st.info(state.message)
elif state.status == "error":
    st.error(state.message)
else:
    st.success(state.message)
    columns = st.columns(2)
    if state.hillshade_png:
        columns[0].image(str(state.hillshade_png), caption="Hillshade preview")
    if state.geojson_path:
        columns[1].json(state.geojson_path.read_text(encoding="utf-8")[:4000])
    if state.report_path:
        st.subheader("Evidence report")
        st.text(state.report_path.read_text(encoding="utf-8")[:8000])
    registry_path = analysis_dir / "registry.sqlite3"
    if registry_path.exists():
        from terra_scout.registry.store import CandidateStore

        store = CandidateStore(registry_path)
        st.subheader("Human review")
        statuses: tuple[str, ...] = (
            "unreviewed",
            "likely_natural",
            "likely_modern",
            "needs_research",
            "potential_anthropogenic_feature",
            "expert_reviewed",
            "rejected",
        )
        for candidate in store.list_candidates():
            choice = st.selectbox(
                f"{candidate.feature_category} {candidate.candidate_id[:8]} "
                f"(score {candidate.anomaly_score:.2f})",
                options=list(statuses),
                index=list(statuses).index(candidate.review_status),
                key=f"review-{candidate.candidate_id}",
            )
            if choice != candidate.review_status:
                store.set_review_status(candidate.candidate_id, choice)  # type: ignore[arg-type]
    else:
        st.caption("No local registry.sqlite3 in this directory yet.")
    st.caption(f"Candidates: {state.candidate_count}. Review stays on this machine.")
