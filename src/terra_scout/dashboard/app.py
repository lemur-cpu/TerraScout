from __future__ import annotations

import importlib

import streamlit as st

from terra_scout.dashboard import copy as _dashboard_copy
from terra_scout.dashboard import (
    pages_briefing,
    pages_coverage,
    pages_explore,
    pages_investigate,
)
from terra_scout.dashboard import shell as _dashboard_shell
from terra_scout.dashboard.theme import CONSOLE_CSS

# Streamlit reruns this file but keeps sys.modules. Reload helpers so a hot
# save cannot ImportError on a name that exists on disk.
_dashboard_copy = importlib.reload(_dashboard_copy)
_dashboard_shell = importlib.reload(_dashboard_shell)
pages_briefing = importlib.reload(pages_briefing)
pages_coverage = importlib.reload(pages_coverage)
pages_explore = importlib.reload(pages_explore)
pages_investigate = importlib.reload(pages_investigate)

PAGE_TITLE = _dashboard_copy.PAGE_TITLE
ABOUT = _dashboard_copy.ABOUT

st.set_page_config(
    page_title=PAGE_TITLE,
    layout="wide",
    menu_items={
        "Get help": None,
        "Report a bug": None,
        "About": ABOUT,
    },
)
st.markdown(f"<style>{CONSOLE_CSS}</style>", unsafe_allow_html=True)


def _switch_to(page) -> None:
    st.switch_page(page)


def _run_coverage() -> None:
    copy_mod = importlib.reload(_dashboard_copy)
    _dashboard_shell.render_masthead(copy_mod)
    _dashboard_shell.render_sidebar(copy_mod)
    pages_coverage.render_coverage(
        root=pages_coverage.COVERAGE_DEFAULT_ROOT,
        switch_explore=lambda: _switch_to(explore_page),
        copy_mod=copy_mod,
    )


def _run_briefing() -> None:
    copy_mod = importlib.reload(_dashboard_copy)
    _dashboard_shell.render_masthead(copy_mod)
    analysis_dir, dem_override = _dashboard_shell.render_sidebar(copy_mod)
    del dem_override
    state = _dashboard_shell.load_for_briefing(analysis_dir)
    pages_briefing.render_briefing(
        state,
        copy_mod,
        switch_investigate=lambda: _switch_to(investigate_page),
        switch_explore=lambda: _switch_to(explore_page),
    )


def _run_explore() -> None:
    copy_mod = importlib.reload(_dashboard_copy)
    _dashboard_shell.render_masthead(copy_mod)
    analysis_dir, dem_override = _dashboard_shell.render_sidebar(copy_mod)
    state = _dashboard_shell.load_or_stop(analysis_dir)
    pages_explore.render_explore(
        state,
        copy_mod,
        dem_override=dem_override,
        switch_investigate=lambda: _switch_to(investigate_page),
    )


def _run_investigate() -> None:
    copy_mod = importlib.reload(_dashboard_copy)
    _dashboard_shell.render_masthead(copy_mod)
    analysis_dir, dem_override = _dashboard_shell.render_sidebar(copy_mod)
    del dem_override
    state = _dashboard_shell.load_or_stop(analysis_dir)
    pages_investigate.render_investigate(state, copy_mod)


coverage_page = st.Page(_run_coverage, title="Coverage", default=True)
briefing_page = st.Page(_run_briefing, title="Briefing")
explore_page = st.Page(_run_explore, title="Explore")
investigate_page = st.Page(_run_investigate, title="Investigate")

navigation = st.navigation(
    [coverage_page, briefing_page, explore_page, investigate_page],
)
navigation.run()
