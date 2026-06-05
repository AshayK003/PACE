from datetime import date

import streamlit as st

from app.config import SourceType
from app.output.markdown import render_markdown
from app.output.pdf import render_pdf
from app.ui.components import (
    display_report,
    render_download_buttons,
    show_error,
    show_info,
    show_warning,
)
from app.ui.sidebar import render_sidebar

st.set_page_config(
    page_title="PACE — Precise Analysis and Compilation of Extracts",
    page_icon="⚡",
    layout="wide",
)


def main() -> None:
    render_sidebar()
    st.title("PACE")
    st.caption("Precise Analysis and Compilation of Extracts")

    if "report_data" not in st.session_state:
        st.session_state.report_data = None
    if "md_content" not in st.session_state:
        st.session_state.md_content = None
    if "pdf_bytes" not in st.session_state:
        st.session_state.pdf_bytes = None

    tab_labels = [t.value for t in SourceType]
    tabs = st.tabs(tab_labels)
    source_types = list(SourceType)
    for tab, source_type in zip(tabs, source_types):
        with tab:
            handle_source_input(source_type)


def handle_source_input(source_type: SourceType) -> None:
    if source_type == SourceType.TEXT:
        text = st.text_area("Paste your text here", height=300)
        if st.button("Analyze", key="analyze_text", type="primary"):
            if text.strip():
                _run_analysis(text, source_type)
            else:
                show_warning("Please enter some text to analyze.")
    elif source_type == SourceType.YOUTUBE:
        url = st.text_input("YouTube URL")
        if st.button("Analyze", key="analyze_youtube", type="primary"):
            if url.strip():
                show_info("Fetching transcript... (analysis will appear here once the pipeline is connected)")
            else:
                show_warning("Please enter a YouTube URL.")
    elif source_type == SourceType.PDF:
        uploaded = st.file_uploader("Upload a PDF file", type=["pdf"])
        if uploaded and st.button("Analyze", key="analyze_pdf", type="primary"):
            show_info(f"Processing {uploaded.name}... (analysis will appear here once the pipeline is connected)")
    elif source_type == SourceType.ARTICLE:
        url = st.text_input("Article URL")
        if st.button("Analyze", key="analyze_article", type="primary"):
            if url.strip():
                show_info("Fetching article... (analysis will appear here once the pipeline is connected)")
            else:
                show_warning("Please enter an article URL.")
    elif source_type == SourceType.AUDIO:
        uploaded = st.file_uploader("Upload an audio file", type=["mp3", "wav", "m4a", "ogg"])
        if uploaded:
            show_warning(
                "Audio transcription requires a local environment with ffmpeg. "
                "On Streamlit Cloud, this feature is unavailable."
            )

    if st.session_state.md_content and st.session_state.pdf_bytes:
        st.divider()
        display_report(st.session_state.md_content)
        render_download_buttons(
            st.session_state.md_content,
            st.session_state.pdf_bytes,
        )


def _run_analysis(text: str, source_type: SourceType) -> None:
    report_data = {
        "title": f"Analysis of: {text[:50].strip()}...",
        "source_type": source_type.value,
        "source_url": "",
        "date_analyzed": date.today().isoformat(),
        "executive_summary": "Analysis pending — pipeline not yet connected.",
        "key_takeaways": [],
        "detailed_analysis": "",
        "supporting_evidence": "",
        "frameworks": [],
        "action_items": [],
        "risks": [],
        "notable_quotes": [],
        "missing_but_important": "",
        "final_synthesis": "",
    }
    st.session_state.report_data = report_data
    st.session_state.md_content = render_markdown(report_data)
    st.session_state.pdf_bytes = render_pdf(st.session_state.md_content)
    show_success("Analysis complete!")
    st.rerun()


if __name__ == "__main__":
    main()
