from __future__ import annotations

import streamlit as st


def render_swarm(copy_mod, *, switch_scan) -> None:
    st.subheader(copy_mod.SWARM_HEADING)
    st.caption(copy_mod.SWARM_CAPTION)
    st.markdown(copy_mod.SWARM_BODY)
    if st.button("Back to Scan"):
        switch_scan()