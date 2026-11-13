from __future__ import annotations

import importlib

import matplotlib.pyplot as plt
import streamlit as st

from terra_scout.dashboard import review as _dashboard_review
from terra_scout.dashboard.bookmark import bookmark_candidate
from terra_scout.dashboard.geometric import refresh_geometric_detection
from terra_scout.dashboard.loader import DashboardState
from terra_scout.dashboard.manifest import resolve_dem_path
from terra_scout.io.dem import load_dem
from terra_scout.registry.store import CandidateStore


def render_explore(
    state: DashboardState,
    copy_mod,
    *,
    dem_override: str | None,
    switch_investigate,
) -> None:
    review = importlib.reload(_dashboard_review)
    st.subheader(copy_mod.EXPLORE_HEADING)
    st.caption(copy_mod.EXPLORE_CAPTION)

    layer_keys = [name for name in review.LAYER_LABELS if name in state.layer_paths]
    if not layer_keys and "hillshade" in state.layer_paths:
        layer_keys = ["hillshade"]

    if layer_keys:
        layer_name = st.radio(
            "CHANNEL",
            layer_keys,
            format_func=lambda key: review.LAYER_LABELS.get(key, key),
            horizontal=True,
        )
        figure = review.render_layer_with_candidates(
            state.layer_paths[layer_name],
            state.candidates,
            None,
        )
        st.pyplot(figure, width="stretch")
        plt.close(figure)
    elif state.hillshade_png:
        st.image(str(state.hillshade_png), caption="Hillshade preview")
    else:
        st.info("No terrain layers in this directory.")

    if state.map_path:
        st.markdown("**Local map**")
        st.caption("Stays on this machine. Do not publish unpublished coordinates.")
        st.iframe(state.map_path, height=420)

    run_root = state.run_root
    product_root = state.product_root
    dem_path = resolve_dem_path(run_root, dem_override) if run_root else None

    st.markdown("**Bookmark place as candidate**")
    if dem_path is None:
        st.warning(copy_mod.DEM_MISSING)
    else:
        col_e, col_n = st.columns(2)
        easting = col_e.number_input("Easting (DEM CRS)", value=0.0, format="%.3f")
        northing = col_n.number_input("Northing (DEM CRS)", value=0.0, format="%.3f")
        if st.button("Bookmark as candidate site"):
            dem = load_dem(dem_path)
            candidate = bookmark_candidate(easting=easting, northing=northing, dem=dem)
            assert product_root is not None
            CandidateStore(product_root / "registry.sqlite3").add_candidates([candidate])
            st.success(f"Bookmarked {candidate.candidate_id} (not a confirmed site).")
            st.rerun()

    st.markdown("**Geometric detection**")
    st.caption("Full DEM. Sync. Replaces non-bookmark registry rows. Not archaeology.")
    if dem_path is None or product_root is None:
        st.warning(copy_mod.DEM_MISSING)
    elif st.button("Run geometric detection on this DEM"):
        refresh_geometric_detection(dem_path=dem_path, product_root=product_root)
        st.success("Geometric detection refreshed. Bookmarks kept.")
        st.rerun()

    if state.candidates:
        st.markdown("**Open in Investigate**")
        labels = [review.queue_label(item) for item in state.candidates]
        chosen = st.selectbox("Candidate sites", labels)
        selected = state.candidates[labels.index(chosen)]
        if st.button("Investigate selected"):
            st.session_state.selected_candidate_id = selected.candidate_id
            switch_investigate()
