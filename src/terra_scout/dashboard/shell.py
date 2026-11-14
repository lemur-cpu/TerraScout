from __future__ import annotations

import importlib
from pathlib import Path

import streamlit as st

from terra_scout.dashboard import copy as _dashboard_copy
from terra_scout.dashboard.loader import DashboardState, load_analysis_directory
from terra_scout.dashboard.theme import CONSOLE_CSS


def reload_copy():
    module = importlib.reload(_dashboard_copy)
    return module


def apply_theme() -> None:
    st.markdown(f"<style>{CONSOLE_CSS}</style>", unsafe_allow_html=True)


def render_masthead(copy_mod) -> None:
    st.markdown('<p class="ts-masthead">TERRASCOUT</p>', unsafe_allow_html=True)
    st.caption(copy_mod.CAPTION)
    st.warning(copy_mod.WARNING)


DATA_PATH_KEY = "ts_data_path"
DATA_PATH_PENDING_KEY = "ts_data_path_pending"


def default_data_path() -> str:
    """Prefer an existing USGS study output when present."""
    study = Path("output/study")
    if (study / "registry.sqlite3").exists():
        return "output/study"
    return "output/analyze"


def queue_data_path(state: dict, path: str | Path) -> None:
    """Schedule a DATA PATH change for the next run (before the widget exists)."""
    state[DATA_PATH_PENDING_KEY] = str(path)


def apply_pending_data_path(state: dict) -> None:
    """Apply a queued DATA PATH before instantiating the sidebar widget."""
    pending = state.pop(DATA_PATH_PENDING_KEY, None)
    if pending is not None:
        state[DATA_PATH_KEY] = str(pending)


def render_sidebar(copy_mod) -> tuple[Path, str | None]:
    # key-only widgets: passing value= with key= resets the field on page switches.
    # Acquire queues a path via DATA_PATH_PENDING_KEY; apply it before the widget.
    apply_pending_data_path(st.session_state)
    if DATA_PATH_KEY not in st.session_state:
        st.session_state[DATA_PATH_KEY] = default_data_path()
    if "ts_dem_override" not in st.session_state:
        st.session_state.ts_dem_override = ""
    analysis_dir = Path(st.sidebar.text_input("DATA PATH", key=DATA_PATH_KEY))
    dem_override = st.sidebar.text_input(
        "DEM PATH (override)",
        key="ts_dem_override",
        help="Used when run_manifest.json is missing or wrong.",
    )
    st.sidebar.caption(copy_mod.LOOP_CAPTION)
    override = dem_override.strip() or None
    return analysis_dir, override


def load_state(analysis_dir: Path) -> DashboardState:
    """Load dashboard state without stopping (Briefing may show acquire UI)."""
    return load_analysis_directory(analysis_dir)


def load_for_briefing(analysis_dir: Path) -> DashboardState:
    state = load_analysis_directory(analysis_dir)
    if state.status == "empty":
        return state
    if state.status == "error" and "does not exist" in state.message:
        return DashboardState(
            status="empty",
            message=state.message,
            run_root=analysis_dir,
        )
    if state.status == "error":
        st.error(state.message)
        st.stop()
    return state


def load_or_stop(analysis_dir: Path, *, allow_empty: bool = False) -> DashboardState:
    if allow_empty:
        return load_for_briefing(analysis_dir)
    state = load_analysis_directory(analysis_dir)
    if state.status == "empty":
        st.info(state.message)
        st.stop()
    if state.status == "error":
        st.error(state.message)
        st.stop()
    return state
