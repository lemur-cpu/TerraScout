from __future__ import annotations

import streamlit as st

from terra_scout.dashboard.loader import DashboardState
from terra_scout.dashboard.traces import load_agent_traces


def render_briefing(state: DashboardState, copy_mod, *, switch_investigate) -> None:
    st.subheader(copy_mod.BRIEFING_HEADING)
    st.caption(copy_mod.BRIEFING_CAPTION)
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
