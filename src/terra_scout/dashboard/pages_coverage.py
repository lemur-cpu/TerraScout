from __future__ import annotations

from pathlib import Path

import streamlit as st

from terra_scout.config import get_settings
from terra_scout.coverage.grid import parse_tile_id
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

    allow_rescan_seed = st.checkbox(
        "Allow re-scan when seeding demo (re-queue scanned demo cells)",
        value=False,
    )

    if st.button("Seed demo tiles"):
        added = index.enqueue_demo_seed(allow_scanned=allow_rescan_seed)
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

    failed_skipped_ids = sorted(
        tile.tile_id for tile in tiles if tile.status in ("failed", "skipped")
    )
    if failed_skipped_ids:
        requeue_failed = st.multiselect(
            "Re-queue failed or skipped tiles",
            options=failed_skipped_ids,
            key="cov_requeue_failed_skipped",
        )
        if st.button("Re-queue selected failed/skipped"):
            added = 0
            for tid in requeue_failed:
                ix, iy = parse_tile_id(tid)
                if index.enqueue(ix, iy):
                    added += 1
            st.success(f"Queued {added} tile(s).")
            st.rerun()

    queued_ids = sorted(tile.tile_id for tile in tiles if tile.status == "queued")
    if queued_ids:
        skip_queued_pick = st.multiselect(
            "Skip queued tiles (mark skipped without downloading)",
            options=queued_ids,
            key="cov_skip_queued",
        )
        if st.button("Skip selected queued"):
            n = 0
            for tid in skip_queued_pick:
                ix, iy = parse_tile_id(tid)
                if index.skip(ix, iy, message="skipped from board"):
                    n += 1
            st.success(f"Skipped {n} tile(s).")
            st.rerun()

    scanned_ids = sorted(tile.tile_id for tile in tiles if tile.status == "scanned")
    if scanned_ids:
        rescan_scanned = st.multiselect(
            "Re-scan scanned tiles (clears prior study folder on next run)",
            options=scanned_ids,
            key="cov_rescan_scanned",
        )
        if st.button("Re-queue selected scanned for re-scan"):
            added = 0
            for tid in rescan_scanned:
                ix, iy = parse_tile_id(tid)
                if index.enqueue(ix, iy, allow_scanned=True):
                    added += 1
            st.success(f"Queued {added} tile(s) for re-scan.")
            st.rerun()

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