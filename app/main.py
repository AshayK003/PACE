import tempfile
from datetime import date
from pathlib import Path

import streamlit as st

from app.config import SourceType
from app.output.markdown import render_markdown
from app.output.pdf import render_pdf
from app.ui.components import display_report, render_download_buttons, show_error, show_info, show_success, show_warning
from app.ui.sidebar import render_sidebar
from app.analyzers.llm_client import LLMClient
from app.analyzers.pipeline import AnalysisPipeline
from app.processors.cleaner import clean_pipeline
from app.processors.chunker import chunk_text


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

    if st.session_state.md_content and st.session_state.pdf_bytes:
        st.divider()
        display_report(st.session_state.md_content)
        render_download_buttons(
            st.session_state.md_content,
            st.session_state.pdf_bytes,
        )


def handle_source_input(source_type: SourceType) -> None:
    if source_type == SourceType.TEXT:
        text = st.text_area("Paste your text here", height=300)
        if st.button("Analyze", key="analyze_text", type="primary"):
            if text.strip():
                _run_analysis(text.strip(), source_type)
            else:
                show_warning("Please enter some text to analyze.")

    elif source_type == SourceType.YOUTUBE:
        url = st.text_input("YouTube URL")
        if st.button("Analyze", key="analyze_youtube", type="primary"):
            if url.strip():
                from app.ingestors.youtube import YouTubeIngestor
                ingestor = YouTubeIngestor()
                if not ingestor.validate(url.strip()):
                    show_error("Invalid YouTube URL.")
                    return
                try:
                    result = ingestor.ingest(url.strip())
                    text = result["text"]
                    metadata = result.get("metadata", {})
                    _run_analysis(text, source_type, source_url=url.strip(), metadata=metadata)
                except Exception as e:
                    show_error(str(e))
            else:
                show_warning("Please enter a YouTube URL.")

    elif source_type == SourceType.PDF:
        uploaded = st.file_uploader("Upload a PDF file", type=["pdf"])
        if uploaded and st.button("Analyze", key="analyze_pdf", type="primary"):
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(uploaded.getvalue())
                tmp_path = tmp.name
            try:
                from app.ingestors.pdf import PDFIngestor
                ingestor = PDFIngestor()
                if not ingestor.validate(tmp_path):
                    show_error("Invalid PDF file.")
                    return
                result = ingestor.ingest(tmp_path)
                _run_analysis(result["text"], source_type, title=uploaded.name)
            except Exception as e:
                show_error(str(e))
            finally:
                Path(tmp_path).unlink(missing_ok=True)

    elif source_type == SourceType.ARTICLE:
        url = st.text_input("Article URL")
        if st.button("Analyze", key="analyze_article", type="primary"):
            if url.strip():
                from app.ingestors.article import ArticleIngestor
                ingestor = ArticleIngestor()
                if not ingestor.validate(url.strip()):
                    show_error("Invalid URL.")
                    return
                try:
                    result = ingestor.ingest(url.strip())
                    if not result.get("text", "").strip():
                        show_error("Could not extract article content.")
                        return
                    _run_analysis(result["text"], source_type, source_url=url.strip())
                except Exception as e:
                    show_error(str(e))
            else:
                show_warning("Please enter an article URL.")

    elif source_type == SourceType.AUDIO:
        uploaded = st.file_uploader("Upload an audio file", type=["mp3", "wav", "m4a", "ogg"])
        if uploaded and st.button("Analyze", key="analyze_audio", type="primary"):
            with tempfile.NamedTemporaryFile(suffix=Path(uploaded.name).suffix, delete=False) as tmp:
                tmp.write(uploaded.getvalue())
                tmp_path = tmp.name
            try:
                from app.ingestors.audio import AudioIngestor
                ingestor = AudioIngestor()
                result = ingestor.ingest(tmp_path)
                text = result.get("text", "")
                if not text.strip():
                    show_warning("Audio transcription requires ffmpeg. Run locally.")
                    return
                _run_analysis(text, source_type, title=uploaded.name)
            except Exception as e:
                show_error(str(e))
            finally:
                Path(tmp_path).unlink(missing_ok=True)


def _run_analysis(content: str, source_type: SourceType, source_url: str = "", title: str = "", metadata: dict | None = None) -> None:
    status_placeholder = st.status("Processing...")
    progress_bar = st.progress(0)
    api_key = st.session_state.get("api_key") or None

    try:
        lang = (metadata or {}).get("language", "")
        lang_lower = str(lang).strip().lower()[:2] if lang else "en"
        _ENGLISH_CODES = {"en", "eng", "english", ""}
        if lang_lower not in _ENGLISH_CODES and lang_lower:
            status_placeholder.update(label=f"Translating from {lang} to English...")
            progress_bar.progress(0.03)
            try:
                client = LLMClient(api_key=api_key)
                content = client.translate_text(content, lang)
            except Exception:
                status_placeholder.update(label="Translation failed, proceeding with original text...")

        status_placeholder.update(label="Cleaning text...")
        cleaned = clean_pipeline(content)

        status_placeholder.update(label="Chunking text...")
        progress_bar.progress(0.15)
        chunk_size = st.session_state.get("chunk_size", 2000)
        chunks = chunk_text(cleaned, chunk_size=chunk_size)
        full_text = " ".join(chunks)

        status_placeholder.update(label="Analyzing content...")
        pipeline = AnalysisPipeline(client=LLMClient(api_key=api_key))

        def on_progress(step_name: str, progress: float) -> None:
            weight = 0.15 + progress * 0.70
            progress_bar.progress(min(weight, 0.85))
            status_placeholder.update(label=f"Analyzing: {step_name.replace('_', ' ').title()}")

        results = pipeline.run_all(full_text, progress_callback=on_progress)

        status_placeholder.update(label="Rendering report...")
        progress_bar.progress(0.90)

        display_title = title or (f"Analysis of: {content[:60].strip()}..." if len(content) > 60 else content)
        report_data = {
            "title": display_title,
            "source_type": source_type.value,
            "source_url": source_url,
            "date_analyzed": date.today().isoformat(),
        }
        report_data.update(results)

        st.session_state.report_data = report_data
        st.session_state.md_content = render_markdown(report_data)
        st.session_state.pdf_bytes = render_pdf(st.session_state.md_content)

        progress_bar.progress(1.0)
        status_placeholder.update(label="Analysis complete!", state="complete")
        show_success("Analysis complete!")
        st.rerun()

    except Exception as e:
        status_placeholder.update(label="Analysis failed", state="error")
        show_error(f"Analysis failed: {e}")


if __name__ == "__main__":
    main()
