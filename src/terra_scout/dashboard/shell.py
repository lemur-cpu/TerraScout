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


def render_sidebar(copy_mod) -> tuple[Path, str | None]:
    default_dir = Path("output/analyze")
    analysis_dir = Path(
        st.sidebar.text_input("DATA PATH", value=str(default_dir), key="ts_data_path")
    )
    dem_override = st.sidebar.text_input(
        "DEM PATH (override)",
        value="",
        key="ts_dem_override",
        help="Used when run_manifest.json is missing or wrong.",
    )
    st.sidebar.caption(copy_mod.LOOP_CAPTION)
    override = dem_override.strip() or None
    return analysis_dir, override


def load_state(analysis_dir: Path) -> DashboardState:
    """Load dashboard state without stopping (Briefing may show acquire UI)."""
    return load_analysis_directory(analysis_dir)


def load_or_stop(analysis_dir: Path, *, allow_empty: bool = False) -> DashboardState:
    state = load_analysis_directory(analysis_dir)
    if allow_empty and state.status == "empty":
        return state
    if allow_empty and state.status == "error" and "does not exist" in state.message:
        # Briefing can acquire into a path that does not exist yet.
        return DashboardState(
            status="empty",
            message=state.message,
            run_root=analysis_dir,
        )
    if state.status == "empty":
        st.info(state.message)
        st.stop()
    if state.status == "error":
        st.error(state.message)
        st.stop()
    return state
