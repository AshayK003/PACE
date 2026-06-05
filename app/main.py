import tempfile
from datetime import date
from pathlib import Path

import streamlit as st

from app.config import SourceType, safe_filename
from app.output.markdown import render_markdown
from app.output.pdf import render_pdf
from app.ui.components import display_report, render_download_buttons, render_empty_state, show_error, show_info, show_success, show_warning
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

    has_report = st.session_state.md_content and st.session_state.pdf_bytes

    if not has_report:
        render_empty_state()

    tab_labels = [t.value for t in SourceType]
    tabs = st.tabs(tab_labels)
    source_types = list(SourceType)
    for tab, source_type in zip(tabs, source_types):
        with tab:
            handle_source_input(source_type)

    if has_report:
        st.divider()
        display_report(st.session_state.md_content)
        render_download_buttons(
            st.session_state.md_content,
            st.session_state.pdf_bytes,
            filename_base=st.session_state.get("filename_base", "report"),
        )


def _validate_url(url: str, patterns: list[str]) -> bool:
    return any(p in url for p in patterns)


def _show_preview(text: str, label: str = "Extracted content") -> None:
    preview = text[:300].strip()
    with st.expander(f"{label} ({len(text):,} characters)", expanded=False):
        st.text(preview + ("..." if len(text) > 300 else ""))


def handle_source_input(source_type: SourceType) -> None:
    if source_type == SourceType.TEXT:
        text = st.text_area("Enter text to analyze", height=250)
        if st.button("Analyze", key="analyze_text", type="primary"):
            if text.strip():
                _run_analysis(text.strip(), source_type)
            else:
                show_warning("Please enter some text to analyze.")

    elif source_type == SourceType.YOUTUBE:
        url = st.text_input(
            "YouTube URL",
            placeholder="https://youtube.com/watch?v=...",
            help="Paste the full URL of a YouTube video.",
        )
        if url.strip():
            valid = _validate_url(url, ["youtube.com/watch?", "youtu.be/", "m.youtube.com/watch?"])
            if valid:
                show_info("\u2705 Valid YouTube URL.")
            else:
                show_warning("\u26a0\ufe0f Does not look like a YouTube URL.")

        if st.button("Analyze", key="analyze_youtube", type="primary"):
            if not url.strip():
                show_warning("Please enter a YouTube URL.")
                return
            from app.ingestors.youtube import YouTubeIngestor
            ingestor = YouTubeIngestor()
            if not ingestor.validate(url.strip()):
                show_error("Invalid YouTube URL. Check the link and try again.")
                return
            try:
                result = ingestor.ingest(url.strip())
                text = result["text"]
                metadata = result.get("metadata", {})
                _show_preview(text, "YouTube transcript")
                _run_analysis(text, source_type, source_url=url.strip(), metadata=metadata)
            except Exception as e:
                show_error(f"Could not fetch transcript: {e}")

    elif source_type == SourceType.PDF:
        uploaded = st.file_uploader("Upload a PDF file", type=["pdf"])
        if uploaded:
            show_info(f"File: **{uploaded.name}** ({uploaded.size / 1024:.0f} KB)")
        if uploaded and st.button("Analyze", key="analyze_pdf", type="primary"):
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(uploaded.getvalue())
                tmp_path = tmp.name
            try:
                from app.ingestors.pdf import PDFIngestor
                ingestor = PDFIngestor()
                if not ingestor.validate(tmp_path):
                    show_error("Could not read this PDF. The file may be corrupted or password-protected.")
                    return
                result = ingestor.ingest(tmp_path)
                _show_preview(result["text"], "PDF content")
                _run_analysis(result["text"], source_type, title=uploaded.name)
            except Exception as e:
                show_error(f"Could not process PDF: {e}")
            finally:
                Path(tmp_path).unlink(missing_ok=True)

    elif source_type == SourceType.ARTICLE:
        url = st.text_input(
            "Article URL",
            placeholder="https://example.com/article",
            help="Enter the full URL of a web article.",
        )
        if url.strip() and not url.startswith(("http://", "https://")):
            show_warning("\u26a0\ufe0f URL should start with http:// or https://")

        if st.button("Analyze", key="analyze_article", type="primary"):
            if not url.strip():
                show_warning("Please enter an article URL.")
                return
            from app.ingestors.article import ArticleIngestor
            ingestor = ArticleIngestor()
            if not ingestor.validate(url.strip()):
                show_error("Invalid URL. Make sure it starts with http:// or https://.")
                return
            try:
                result = ingestor.ingest(url.strip())
                if not result.get("text", "").strip():
                    show_error("Could not extract article content. The page may be behind a paywall.")
                    return
                _show_preview(result["text"], "Article content")
                _run_analysis(result["text"], source_type, source_url=url.strip())
            except Exception as e:
                show_error(f"Could not fetch article: {e}")

    elif source_type == SourceType.AUDIO:
        uploaded = st.file_uploader("Upload an audio file", type=["mp3", "wav", "m4a", "ogg"])
        if uploaded:
            show_info(f"File: **{uploaded.name}** ({uploaded.size / 1024:.0f} KB)")
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
                    show_warning("Audio transcription requires ffmpeg. Run this app locally with ffmpeg installed.")
                    return
                _show_preview(text, "Transcribed audio")
                _run_analysis(text, source_type, title=uploaded.name)
            except Exception as e:
                show_error(f"Could not transcribe audio: {e}")
            finally:
                Path(tmp_path).unlink(missing_ok=True)


def _run_analysis(content: str, source_type: SourceType, source_url: str = "", title: str = "", metadata: dict | None = None) -> None:
    status = st.status("Starting analysis...", expanded=True)
    progress_bar = st.progress(0.0)
    api_key = st.session_state.get("api_key") or None
    client = LLMClient(api_key=api_key)

    try:
        lang = (metadata or {}).get("language", "")
        lang_lower = str(lang).strip().lower()[:2] if lang else "en"
        _ENGLISH_CODES = {"en", "eng", "english", ""}
        if lang_lower not in _ENGLISH_CODES and lang_lower:
            status.write(f"\U0001f310 Translating from {lang} to English...")
            progress_bar.progress(0.03)
            try:
                content = client.translate_text(content, lang)
            except Exception:
                status.write("Translation failed, proceeding with original text.")

        status.write(f"\U0001f9f9 Cleaning text ({len(content):,} characters)...")
        progress_bar.progress(0.08)
        cleaned = clean_pipeline(content)

        status.write(f"\u2702\ufe0f Chunking text...")
        progress_bar.progress(0.15)
        chunk_size = st.session_state.get("chunk_size", 2000)
        chunks = chunk_text(cleaned, chunk_size=chunk_size)
        full_text = " ".join(chunks)
        status.write(f"Split into {len(chunks)} chunk(s)")

        status.write("\U0001f916 Running AI analysis...")
        pipeline = AnalysisPipeline(client=client)

        def on_progress(step_name: str, progress: float) -> None:
            weight = 0.15 + progress * 0.70
            progress_bar.progress(min(weight, 0.85))
            status.write(f"  \u2022 {step_name.replace('_', ' ').title()}")

        results = pipeline.run_all(full_text, progress_callback=on_progress)

        status.write("\U0001f4dd Rendering report...")
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
        st.session_state.filename_base = safe_filename(display_title)
        st.session_state.md_content = render_markdown(report_data)
        st.session_state.pdf_bytes = render_pdf(
            st.session_state.md_content,
            title=display_title,
            source_type=source_type.value,
            source_url=source_url or "",
            date_analyzed=date.today().isoformat(),
        )

        progress_bar.progress(1.0)
        status.update(label="Analysis complete!", state="complete")
        show_success("Report ready \u2014 scroll down to view.")
        st.rerun()

    except Exception as e:
        progress_bar.empty()
        status.update(label="Analysis failed", state="error")
        msg = str(e)
        if "401" in msg or "unauthorized" in msg.lower() or "api key" in msg.lower():
            status.write("Authentication error. Check your API key in Settings.")
        elif "timeout" in msg.lower() or "timed out" in msg.lower():
            status.write("The request timed out. The content may be too long. Try a smaller chunk size.")
        else:
            status.write(f"Error: {msg}")
        show_error("Analysis failed. See the status panel above for details.")


if __name__ == "__main__":
    main()
