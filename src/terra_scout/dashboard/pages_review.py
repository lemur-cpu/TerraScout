from __future__ import annotations

import streamlit as st


def render_review(copy_mod, *, switch_investigate) -> None:
    st.subheader(copy_mod.REVIEW_HEADING)
    st.caption(copy_mod.REVIEW_CAPTION)
    st.markdown(copy_mod.REVIEW_BODY)
    if st.button(copy_mod.REVIEW_INVESTIGATE_CTA):
        switch_investigate()