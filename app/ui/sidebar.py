import streamlit as st


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### PACE")
        st.caption("AI-powered content analysis")

        with st.expander("Settings", expanded=False):
            st.slider(
                "Chunk size",
                min_value=500,
                max_value=4000,
                value=2000,
                step=100,
                key="chunk_size",
                help="Larger chunks give more context per analysis step but use more tokens.",
            )

        with st.expander("LLM Settings", expanded=False):
            st.text_input(
                "API Key",
                type="password",
                key="api_key",
                placeholder="Optional — leave empty for default key",
                help="Enter a custom API key to override the default. Your key is never stored.",
            )

        st.divider()
        st.markdown(
            "Analyze YouTube videos, PDFs, web articles, "
            "audio files, or raw text into structured reports."
        )
