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
    st.caption(
        f"Candidates: {state.candidate_count}. "
        "Review status changes belong in the SQLite registry."
    )
