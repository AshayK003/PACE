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


def render_download_buttons(
    md_content: str,
    pdf_bytes: bytes,
    epub_bytes: bytes,
    obsidian_content: str,
    filename_base: str = "report",
) -> None:
    export_path = st.session_state.get("export_path")
    if export_path:
        base = export_path["slug"]
    else:
        base = filename_base

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.download_button(
            label="Markdown",
            data=md_content,
            file_name=f"{base}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            label="PDF",
            data=pdf_bytes,
            file_name=f"{base}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    with col3:
        st.download_button(
            label="EPUB",
            data=epub_bytes,
            file_name=f"{base}.epub",
            mime="application/epub+zip",
            use_container_width=True,
        )
    with col4:
        st.download_button(
            label="Obsidian",
            data=obsidian_content,
            file_name=f"{base}.md",
            mime="text/markdown",
            use_container_width=True,
            help="YAML frontmatter for Obsidian vault",
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
