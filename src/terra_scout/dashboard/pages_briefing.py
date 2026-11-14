from __future__ import annotations

from pathlib import Path

import streamlit as st

from terra_scout.config import get_settings
from terra_scout.dashboard.acquire import DEMO_BBOX, AcquireError, acquire_and_analyze
from terra_scout.dashboard.loader import DashboardState
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
    st.markdown(f"**{copy_mod.ACQUIRE_HEADING}**")
    st.caption(copy_mod.ACQUIRE_CAPTION)
    st.info(copy_mod.ACQUIRE_NOTE)
    if st.button("Load demo bbox", help=copy_mod.ACQUIRE_DEMO_HELP):
        st.session_state["ts_acq_west"] = DEMO_BBOX[0]
        st.session_state["ts_acq_south"] = DEMO_BBOX[1]
        st.session_state["ts_acq_east"] = DEMO_BBOX[2]
        st.session_state["ts_acq_north"] = DEMO_BBOX[3]
        st.rerun()
    cols = st.columns(4)
    west = cols[0].number_input(
        "west", value=float(st.session_state.get("ts_acq_west", DEMO_BBOX[0])), key="ts_acq_west"
    )
    south = cols[1].number_input(
        "south",
        value=float(st.session_state.get("ts_acq_south", DEMO_BBOX[1])),
        key="ts_acq_south",
    )
    east = cols[2].number_input(
        "east", value=float(st.session_state.get("ts_acq_east", DEMO_BBOX[2])), key="ts_acq_east"
    )
    north = cols[3].number_input(
        "north",
        value=float(st.session_state.get("ts_acq_north", DEMO_BBOX[3])),
        key="ts_acq_north",
    )
    settings = get_settings()
    output_dir = Path(
        st.text_input(
            "Output directory",
            value=str(st.session_state.get("ts_acquire_output", "output/study")),
            key="ts_acquire_output",
        )
    )
    max_mb = st.number_input(
        "Max download MB",
        min_value=0.1,
        value=float(settings.max_download_megabytes),
        step=1.0,
        key="ts_acquire_max_mb",
    )
    if st.button("Download 3DEP + analyze", type="primary"):
        try:
            with st.spinner("Downloading 3DEP and running analyze…"):
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
        st.session_state.ts_data_path = str(result.output_dir)
        st.success(
            f"Acquire finished ({result.observation_kind}, {result.candidate_count} candidates)."
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
