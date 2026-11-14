from __future__ import annotations

from pathlib import Path

import streamlit as st

from terra_scout.config import get_settings
from terra_scout.dashboard.acquire import DEMO_BBOX, AcquireError, acquire_and_analyze
from terra_scout.dashboard.loader import DashboardState
from terra_scout.dashboard.shell import queue_data_path
from terra_scout.dashboard.traces import load_agent_traces
from terra_scout.data.usgs import DownloadLimitExceeded


def render_briefing(
    state: DashboardState,
    copy_mod,
    *,
    switch_investigate,
    switch_explore=None,
) -> None:
    st.subheader(copy_mod.BRIEFING_HEADING)
    st.caption(copy_mod.BRIEFING_CAPTION)

    default_out = Path(st.session_state.get("ts_acquire_output", "output/study"))
    analysis_dir = state.run_root or default_out
    _render_acquire_panel(copy_mod, analysis_dir=Path(analysis_dir), switch_explore=switch_explore)

    if state.status == "empty":
        st.info(state.message)
        return
    if state.status == "error":
        st.error(state.message)
        return

    st.caption(
        f"OBS.KIND  {state.observation_kind.upper()}  ·  LAYOUT  {state.layout_kind.upper()}"
    )
    st.write(f"Run root: `{state.run_root}`")
    if state.product_root and state.product_root != state.run_root:
        st.write(f"Products: `{state.product_root}`")

    st.markdown("**Inventory**")
    for key, present in state.inventory.items():
        mark = "YES" if present else "no"
        st.write(f"- {key}: {mark}")

    st.markdown("**Candidate counts by review_status**")
    if state.status_counts:
        for status, count in sorted(state.status_counts.items()):
            st.write(f"- {status}: {count}")
    else:
        st.write("No registry candidates.")
    st.caption(state.message)

    st.markdown("**Last swarm summary**")
    _render_swarm_summary(state, copy_mod)

    if state.next_unreviewed_id:
        if st.button("Open next unreviewed", type="primary"):
            st.session_state.selected_candidate_id = state.next_unreviewed_id
            switch_investigate()
    else:
        st.caption("No unreviewed candidate sites to open.")


def _render_acquire_panel(copy_mod, *, analysis_dir: Path, switch_explore) -> None:
    del analysis_dir
    st.markdown(f"**{copy_mod.ACQUIRE_HEADING}**")
    st.caption(copy_mod.ACQUIRE_CAPTION)
    st.caption(copy_mod.ACQUIRE_NOTE)

    defaults = {
        "ts_acq_west": DEMO_BBOX[0],
        "ts_acq_south": DEMO_BBOX[1],
        "ts_acq_east": DEMO_BBOX[2],
        "ts_acq_north": DEMO_BBOX[3],
        "ts_acquire_output": "output/study",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    if "ts_acquire_max_mb" not in st.session_state:
        st.session_state.ts_acquire_max_mb = float(
            min(get_settings().max_download_megabytes, 5.0)
        )

    if st.button("Load demo bbox", help=copy_mod.ACQUIRE_DEMO_HELP):
        st.session_state.ts_acq_west = DEMO_BBOX[0]
        st.session_state.ts_acq_south = DEMO_BBOX[1]
        st.session_state.ts_acq_east = DEMO_BBOX[2]
        st.session_state.ts_acq_north = DEMO_BBOX[3]
        st.rerun()

    cols = st.columns(4)
    west = cols[0].number_input("West", format="%.6f", key="ts_acq_west")
    south = cols[1].number_input("South", format="%.6f", key="ts_acq_south")
    east = cols[2].number_input("East", format="%.6f", key="ts_acq_east")
    north = cols[3].number_input("North", format="%.6f", key="ts_acq_north")

    settings = get_settings()
    output_dir = Path(st.text_input("Output directory", key="ts_acquire_output"))
    max_mb = st.number_input(
        "Max download (MB)",
        min_value=0.5,
        step=0.5,
        key="ts_acquire_max_mb",
    )
    if st.button("Download USGS 3DEP and analyze", type="primary"):
        try:
            with st.spinner("Downloading DEM and running detection…"):
                result = acquire_and_analyze(
                    west=float(west),
                    south=float(south),
                    east=float(east),
                    north=float(north),
                    cache_dir=Path(settings.cache_dir),
                    output_dir=output_dir,
                    max_megabytes=float(max_mb),
                )
        except (AcquireError, DownloadLimitExceeded, OSError, RuntimeError) as error:
            st.error(str(error))
            return
        queue_data_path(st.session_state, result.output_dir)
        st.success(
            f"Wrote {result.candidate_count} candidate site(s) to `{result.output_dir}` "
            f"from `{result.dem_path.name}` ({result.observation_kind}). "
            "Not archaeological confirmation."
        )
        st.rerun()
    if switch_explore is not None and st.button("Open Explore"):
        switch_explore()


def _render_swarm_summary(state: DashboardState, copy_mod) -> None:
    run_root = state.run_root
    if run_root is None:
        st.caption("No run root.")
        return
    traces_path = run_root / "agent_traces.json"
    payload = load_agent_traces(traces_path)
    if payload is not None:
        st.write(f"summary: {payload.get('summary')}")
        st.write(f"llm_was_used: {payload.get('llm_was_used')}")
        st.write(f"candidate_count: {payload.get('candidate_count')}")
        for trace in payload.get("traces") or []:
            agent_id = trace.get("agent_id", "?")
            notes = trace.get("notes") or []
            tools = trace.get("tool_calls") or []
            ok = sum(1 for item in tools if item.get("succeeded"))
            st.write(f"- {agent_id}: tools_ok={ok}/{len(tools)} notes={len(notes)}")
        if state.report_path:
            st.caption(f"Report: `{state.report_path}`")
        return
    if state.report_path and state.report_path.name == "swarm_report.md":
        excerpt = state.report_path.read_text(encoding="utf-8")[:1200]
        st.text(excerpt)
        st.caption("Structured traces need an agents run (agent_traces.json).")
        return
    st.caption("No swarm run in this directory.")
