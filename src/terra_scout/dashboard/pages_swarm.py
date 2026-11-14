from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import streamlit as st

from terra_scout.dashboard import shell
from terra_scout.dashboard.swarm_run import (
    SwarmRunError,
    attach_swarm_run,
    refresh_swarm_run,
    start_swarm_run,
    stop_swarm_run,
)
from terra_scout.dashboard.swarm_studies import SwarmStudy, list_runnable_studies, resolve_study
from terra_scout.dashboard.traces import agent_status_rows, load_agent_traces

_SELECTED_KEY = "ts_swarm_study_label"


def _study_options(
    coverage_root: Path,
    data_path: Path | None,
) -> list[SwarmStudy]:
    studies = list(list_runnable_studies(coverage_root))
    seen = {s.output_dir for s in studies}
    if data_path is not None:
        extra = resolve_study(Path(data_path))
        if extra is not None and extra.output_dir not in seen:
            studies.insert(
                0,
                SwarmStudy(
                    label=f"DATA PATH · {extra.label}",
                    tile_id=extra.tile_id,
                    output_dir=extra.output_dir,
                    dem_path=extra.dem_path,
                ),
            )
    return studies


def _select_study(studies: list[SwarmStudy]) -> SwarmStudy | None:
    if not studies:
        return None
    labels = [s.label for s in studies]
    default = st.session_state.get(_SELECTED_KEY)
    index = labels.index(default) if default in labels else 0
    chosen = st.selectbox("Study", options=labels, index=index, key="ts_swarm_select")
    st.session_state[_SELECTED_KEY] = chosen
    for study in studies:
        if study.label == chosen:
            return study
    return studies[0]


def _queue_and_switch(study: SwarmStudy, switch) -> None:
    shell.queue_data_path(st.session_state, study.output_dir)
    switch()


def _render_agent_table(study: SwarmStudy, run_state: dict | None) -> None:
    traces_payload = load_agent_traces(study.output_dir / "agent_traces.json")
    rows = agent_status_rows(traces_payload, run_state)
    st.dataframe(rows, use_container_width=True, hide_index=True)


def render_swarm(
    copy_mod,
    *,
    switch_scan,
    coverage_root: Path | None = None,
    data_path: Path | None = None,
    switch_investigate=None,
    switch_briefing=None,
) -> None:
    root = Path(coverage_root) if coverage_root is not None else Path("output/coverage")
    st.subheader(copy_mod.SWARM_HEADING)
    st.caption(copy_mod.SWARM_CAPTION)
    st.markdown(copy_mod.SWARM_BODY)
    st.info(copy_mod.SWARM_ETHICS)

    studies = _study_options(root, data_path)
    if not studies:
        st.warning(copy_mod.SWARM_EMPTY)
        if st.button("Back to Scan"):
            switch_scan()
        return

    study = _select_study(studies)
    if study is None:
        st.warning(copy_mod.SWARM_EMPTY)
        return

    if not study.dem_path.is_file():
        st.error(copy_mod.SWARM_NO_DEM)
        return

    st.code(f"DEM: {study.dem_path}\noutput-dir: {study.output_dir}", language=None)

    run_state = refresh_swarm_run(study.output_dir)
    status = (run_state or {}).get("status", "idle")
    st.metric("Run status", status)
    if run_state is not None:
        pid = run_state.get("pid")
        started = run_state.get("started_at")
        finished = run_state.get("finished_at")
        bits = [f"pid={pid}" if pid is not None else None, started, finished]
        st.caption(" · ".join(str(b) for b in bits if b))

    cols = st.columns(4)
    start_clicked = cols[0].button("Start", type="primary")
    attach_clicked = cols[1].button("Attach")
    stop_clicked = cols[2].button("Stop")
    resume_clicked = cols[3].button("Resume")

    st.caption(copy_mod.SWARM_STOP_HELP)
    st.caption(copy_mod.SWARM_RESUME_HELP)

    if start_clicked or resume_clicked:
        try:
            run_state = start_swarm_run(study.dem_path, study.output_dir)
            st.success(f"Started local swarm (pid={run_state.get('pid')})")
            st.rerun()
        except SwarmRunError as error:
            st.error(str(error))

    if attach_clicked:
        run_state = attach_swarm_run(study.output_dir)
        if run_state is None:
            st.warning("No swarm_run.json yet for this study.")
        else:
            st.success(f"Attached — status={run_state.get('status')}")

    if stop_clicked:
        try:
            run_state = stop_swarm_run(study.output_dir)
            st.warning(f"Stopped — status={run_state.get('status')}")
            st.rerun()
        except SwarmRunError as error:
            st.error(str(error))

    poll = int(getattr(copy_mod, "SWARM_POLL_SECONDS", 2))
    if (run_state or {}).get("status") == "running":
        st.caption(f"Polling every ~{poll}s while the local process is running.")

        def _poll_panel() -> None:
            latest = refresh_swarm_run(study.output_dir)
            st.metric("Run status (live)", (latest or {}).get("status", "unknown"))
            _render_agent_table(study, latest)

        fragment = getattr(st, "fragment", None)
        if callable(fragment):
            try:
                decorated = fragment(run_every=timedelta(seconds=poll))(_poll_panel)
                decorated()
            except TypeError:
                _render_agent_table(study, run_state)
        else:
            _render_agent_table(study, run_state)
    else:
        _render_agent_table(study, run_state)

    cta = st.columns(3)
    if cta[0].button("Open Investigate") and switch_investigate is not None:
        _queue_and_switch(study, switch_investigate)
    if cta[1].button("Open Briefing") and switch_briefing is not None:
        _queue_and_switch(study, switch_briefing)
    if cta[2].button("Back to Scan"):
        switch_scan()
