from __future__ import annotations

from pathlib import Path

import streamlit as st

from terra_scout.coverage.index import CoverageIndex
from terra_scout.coverage.progress import coverage_completeness


def render_home(
    *,
    root: Path,
    copy_mod,
    switch_scan,
    switch_swarm,
    switch_review,
    switch_explore,
) -> None:
    st.subheader(copy_mod.HOME_HEADING)
    st.caption(copy_mod.HOME_CAPTION)
    st.markdown(copy_mod.HOME_LOOP)
    st.warning(copy_mod.HOME_ETHICS)

    db_path = root / "coverage.sqlite3"
    index = CoverageIndex(db_path)
    index.ensure_open()
    counts = index.status_counts()
    pct = coverage_completeness(counts)
    st.metric("CONUS scan completeness", f"{pct:.4f}%")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button(copy_mod.HOME_CTA_SCAN):
            switch_scan()
    with c2:
        if st.button(copy_mod.HOME_CTA_SWARM):
            switch_swarm()
    with c3:
        if st.button(copy_mod.HOME_CTA_REVIEW):
            switch_review()
    with c4:
        if st.button(copy_mod.HOME_CTA_EXPLORE):
            switch_explore()