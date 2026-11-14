from __future__ import annotations

from pathlib import Path

import streamlit as st

from terra_scout.config import get_settings
from terra_scout.coverage.index import CoverageIndex
from terra_scout.coverage.process import process_next
from terra_scout.dashboard.shell import queue_data_path

COVERAGE_DEFAULT_ROOT = Path("output/coverage")
COVERAGE_TABLE_LIMIT = 200


def render_coverage(
    *,
    root: Path,
    switch_explore,
    copy_mod,
) -> None:
    st.subheader(copy_mod.COVERAGE_HEADING)
    st.caption(copy_mod.COVERAGE_CAPTION)
    st.markdown(copy_mod.COVERAGE_NOTE)

    db_path = root / "coverage.sqlite3"
    index = CoverageIndex(db_path)
    index.ensure_open()
    counts = index.status_counts()

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Unscanned", counts.get("unscanned", 0))
    c2.metric("Queued", counts.get("queued", 0))
    c3.metric("Running", counts.get("running", 0))
    c4.metric("Scanned", counts.get("scanned", 0))
    c5.metric("Skipped", counts.get("skipped", 0))
    c6.metric("Failed", counts.get("failed", 0))

    settings = get_settings()
    batch_n = st.number_input("Process N queued tiles", min_value=1, max_value=50, value=1)
    max_mb = st.number_input(
        "Max download MB per tile",
        min_value=0.1,
        max_value=500.0,
        value=float(settings.max_download_megabytes),
    )

    if st.button("Seed demo tiles"):
        added = index.enqueue_demo_seed()
        st.success(f"Queued {added} demo tile(s).")
        st.rerun()

    if st.button("Process batch"):
        outcomes = process_next(
            index,
            n=int(batch_n),
            cache_dir=root / "cache",
            max_megabytes=float(max_mb),
            tiles_root=root,
        )
        if not outcomes:
            st.info("No queued tiles.")
        else:
            lines = [f"{item.tile_id}: {item.status}" for item in outcomes]
            st.success("Processed: " + ", ".join(lines))
        st.rerun()

    tiles = index.list_tiles(limit=COVERAGE_TABLE_LIMIT)
    if tiles:
        rows = [
            {
                "tile_id": tile.tile_id,
                "status": tile.status,
                "study_dir": tile.study_dir or "",
                "message": tile.message or "",
            }
            for tile in tiles
        ]
        st.dataframe(rows, use_container_width=True)
        study_dirs = sorted(
            {Path(tile.study_dir) for tile in tiles if tile.study_dir},
            key=lambda path: str(path),
            reverse=True,
        )
        if study_dirs:
            chosen = st.selectbox(
                "Open study in Explore",
                options=study_dirs,
                key="cov_study",
            )
            if st.button("Open Explore for study"):
                queue_data_path(st.session_state, chosen)
                if switch_explore is not None:
                    switch_explore()