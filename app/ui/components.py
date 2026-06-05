import streamlit as st


def render_empty_state() -> None:
    st.markdown("### Welcome to PACE")
    st.markdown(
        "Select a source type above to analyze content into "
        "a structured report with summaries, takeaways, and insights."
    )
    guide = [
        ("\U0001f517", "YouTube", "Paste a video URL to analyze its transcript"),
        ("\U0001f4c4", "PDF", "Upload a PDF document for text extraction"),
        ("\U0001f310", "Article", "Enter a web article URL to extract and analyze"),
        ("\U0001f399\ufe0f", "Audio", "Upload an audio file for transcription (local only)"),
        ("\u270d\ufe0f", "Text", "Paste or type raw text directly"),
    ]
    for icon, label, desc in guide:
        st.markdown(f"**{icon} {label}** — {desc}")


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
    st.markdown("## Report")
    st.markdown(md_content)


def show_error(message: str) -> None:
    st.error(message)


def show_success(message: str) -> None:
    st.success(message)


def show_warning(message: str) -> None:
    st.warning(message)


def show_info(message: str) -> None:
    st.info(message)
