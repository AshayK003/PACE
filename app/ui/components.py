import streamlit as st

from app.config import SourceType


def source_type_selector() -> SourceType:
    options = [t.value for t in SourceType]
    selected = st.selectbox("Select source type", options, index=0)
    return SourceType(selected)


def render_download_buttons(md_content: str, pdf_bytes: bytes, filename_base: str = "report") -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="Download Markdown",
            data=md_content,
            file_name=f"{filename_base}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            label="Download PDF",
            data=pdf_bytes,
            file_name=f"{filename_base}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )


def display_report(md_content: str) -> None:
    st.markdown(md_content)


def show_error(message: str) -> None:
    st.error(message)


def show_success(message: str) -> None:
    st.success(message)


def show_warning(message: str) -> None:
    st.warning(message)


def show_info(message: str) -> None:
    st.info(message)
