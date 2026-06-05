import streamlit as st

from app.config import SourceType


def render_sidebar() -> SourceType:
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/artificial-intelligence.png", width=48)
        st.title("PACE")
        st.caption("Precise Analysis and Compilation of Extracts")
        st.divider()
        source_type = SourceType(st.selectbox(
            "Source Type",
            options=[t.value for t in SourceType],
            index=0,
        ))
        st.divider()
        with st.expander("About", expanded=False):
            st.markdown(
                "**PACE** transforms raw, unstructured information from "
                "long-form content into organized, actionable summaries."
            )
        with st.expander("Settings", expanded=False):
            st.checkbox("Show progress details", value=True, key="show_progress")
            st.slider("Chunk size", min_value=500, max_value=4000, value=2000, step=100, key="chunk_size")
        with st.expander("LLM Settings", expanded=False):
            st.text_input(
                "API Key",
                type="password",
                key="api_key",
                help="Leave empty to use the default key. Your key is not stored.",
            )
        return source_type
