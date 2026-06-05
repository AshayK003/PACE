import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


# ── Base Ingestor Tests ──────────────────────────────────────────────────────

class TestBaseIngestor:
    def test_base_ingestor_cannot_instantiate(self):
        """BaseIngestor should be abstract and not instantiable directly."""
        from app.ingestors.base import BaseIngestor
        with pytest.raises(TypeError):
            BaseIngestor()

    def test_base_ingestor_interface_enforced(self):
        """Subclasses must implement ingest() and validate()."""
        from app.ingestors.base import BaseIngestor
        with pytest.raises(TypeError):
            class BadIngestor(BaseIngestor):
                pass
            BadIngestor()

    def test_concrete_ingestor_works(self):
        """A proper subclass with both methods should instantiate fine."""
        from app.ingestors.base import BaseIngestor
        class GoodIngestor(BaseIngestor):
            def ingest(self, source):
                return {"title": "test", "text": "test", "metadata": {}}
            def validate(self, source):
                return True
        instance = GoodIngestor()
        assert instance.ingest("test") == {"title": "test", "text": "test", "metadata": {}}
        assert instance.validate("test") is True

    def test_ingest_return_structure(self):
        """ingest() must return dict with title, text, metadata keys."""
        from app.ingestors.base import BaseIngestor
        class TestIngestor(BaseIngestor):
            def ingest(self, source):
                return {"title": "x", "text": "y", "metadata": {}}
            def validate(self, source):
                return True
        result = TestIngestor().ingest("x")
        assert "title" in result
        assert "text" in result
        assert "metadata" in result

    def test_validate_accepts_valid_urls(self):
        """validate() must accept valid input types."""
        from app.ingestors.base import BaseIngestor
        class TestIngestor(BaseIngestor):
            def ingest(self, source):
                return {"title": "", "text": "", "metadata": {}}
            def validate(self, source):
                return bool(source)
        ing = TestIngestor()
        assert ing.validate("https://youtube.com/watch?v=abc123") is True
        assert ing.validate("") is False
        assert ing.validate(None) is False


# ── YouTube Ingestor Tests ───────────────────────────────────────────────────

class TestYouTubeIngestor:
    @patch("youtube_transcript_api.YouTubeTranscriptApi")
    def test_ingest_with_transcript(self, mock_api, sample_transcript):
        """Happy path: fetches transcript successfully."""
        instance = mock_api.return_value
        instance.fetch.return_value = sample_transcript
        from app.ingestors.youtube import YouTubeIngestor
        ing = YouTubeIngestor()
        result = ing.ingest("https://youtube.com/watch?v=abc123")
        assert result["title"] == "YouTube Video (abc123)"
        assert "supervised learning" in result["text"]
        assert "reinforcement learning" in result["text"]
        assert result["metadata"]["video_id"] == "abc123"
        assert result["metadata"]["source"] == "transcript"

    @patch("youtube_transcript_api.YouTubeTranscriptApi")
    def test_ingest_without_transcript_falls_back(self, mock_api):
        """When no transcript exists, should raise fallback message."""
        instance = mock_api.return_value
        instance.fetch.side_effect = Exception("No transcript available")
        from app.ingestors.youtube import YouTubeIngestor
        ing = YouTubeIngestor()
        with pytest.raises(Exception, match="No transcript available"):
            ing.ingest("https://youtube.com/watch?v=abc123")

    @pytest.mark.parametrize("url,expected_id", [
        ("https://youtube.com/watch?v=abc123", "abc123"),
        ("https://youtu.be/abc123", "abc123"),
        ("https://www.youtube.com/watch?v=abc123&t=30", "abc123"),
        ("https://m.youtube.com/watch?v=abc123", "abc123"),
    ])
    def test_extract_video_id_common_patterns(self, url, expected_id):
        """Should parse various URL formats."""
        from app.ingestors.youtube import YouTubeIngestor
        ing = YouTubeIngestor()
        assert ing._extract_video_id(url) == expected_id

    @pytest.mark.parametrize("invalid_url", [
        "https://google.com",
        "https://vimeo.com/12345",
        "not-a-url",
        "",
    ])
    def test_extract_video_id_invalid(self, invalid_url):
        """Should return None or raise for non-YouTube URLs."""
        from app.ingestors.youtube import YouTubeIngestor
        ing = YouTubeIngestor()
        assert ing._extract_video_id(invalid_url) is None

    def test_validate_accepts_youtube_urls(self):
        """validate() should accept YouTube domains."""
        from app.ingestors.youtube import YouTubeIngestor
        ing = YouTubeIngestor()
        assert ing.validate("https://youtube.com/watch?v=abc123") is True
        assert ing.validate("https://youtu.be/abc123") is True

    def test_validate_rejects_non_youtube(self):
        """validate() should reject non-YouTube URLs."""
        from app.ingestors.youtube import YouTubeIngestor
        ing = YouTubeIngestor()
        assert ing.validate("https://vimeo.com/12345") is False
        assert ing.validate("") is False

    @patch("youtube_transcript_api.YouTubeTranscriptApi")
    def test_transcript_concatenation(self, mock_api, sample_transcript):
        """Multiple transcript segments should be joined with spaces."""
        instance = mock_api.return_value
        instance.fetch.return_value = sample_transcript
        from app.ingestors.youtube import YouTubeIngestor
        ing = YouTubeIngestor()
        result = ing.ingest("https://youtube.com/watch?v=abc123")
        text = result["text"]
        assert text.startswith("Welcome to this presentation")
        assert text.endswith("reinforcement learning fundamentals.")
        assert "supervised" in text
        assert "unsupervised" in text
        assert len(text.split()) > 10


# ── PDF Ingestor Tests ───────────────────────────────────────────────────────

class TestPDFIngestor:
    @patch("pymupdf4llm.to_markdown")
    def test_ingest_with_pymupdf(self, mock_pymupdf):
        """Happy path: extracts markdown from PDF via PyMuPDF4LLM."""
        mock_pymupdf.return_value = "# Title\n\nBody text.\n\n| A | B |\n|---|---|\n| 1 | 2 |"
        from app.ingestors.pdf import PDFIngestor
        ing = PDFIngestor()
        result = ing.ingest("report.pdf")
        assert result["title"] == "report.pdf"
        assert "Body text" in result["text"]
        assert "|" in result["text"]
        assert result["metadata"]["parser"] == "pymupdf4llm"

    @patch("pymupdf4llm.to_markdown")
    @patch("pdfplumber.open")
    def test_table_supplement(self, mock_plumber, mock_pymupdf, sample_text):
        """Tables from pdfplumber should supplement PyMuPDF4LLM output."""
        mock_pymupdf.return_value = sample_text
        mock_page = MagicMock()
        mock_page.extract_tables.return_value = [["H1", "H2"], ["V1", "V2"]]
        mock_plumber.return_value.__enter__.return_value.pages = [mock_page]
        from app.ingestors.pdf import PDFIngestor
        ing = PDFIngestor()
        result = ing.ingest("report.pdf")
        assert "tables" in result["metadata"]
        assert result["metadata"]["tables_supplemented"] is True

    @patch("pymupdf4llm.to_markdown")
    @patch("pypdf.PdfReader")
    def test_fallback_to_pypdf(self, mock_pdfreader, mock_pymupdf):
        """When PyMuPDF4LLM fails, should fall back to pypdf."""
        mock_pymupdf.side_effect = Exception("Parsing error")
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Fallback PDF text."
        mock_pdfreader.return_value.pages = [mock_page]
        from app.ingestors.pdf import PDFIngestor
        ing = PDFIngestor()
        result = ing.ingest("report.pdf")
        assert result["metadata"]["parser"] == "pypdf"
        assert result["metadata"]["fallback_used"] is True

    def test_validate_pdf_file(self):
        """validate() should accept .pdf paths and reject others."""
        from app.ingestors.pdf import PDFIngestor
        ing = PDFIngestor()
        assert ing.validate("document.pdf") is True
        assert ing.validate(Path("document.pdf")) is True
        assert ing.validate("document.txt") is False
        assert ing.validate("") is False

    def test_ingest_missing_file(self):
        """Should raise FileNotFoundError for non-existent file."""
        from app.ingestors.pdf import PDFIngestor
        ing = PDFIngestor()
        with pytest.raises((FileNotFoundError, Exception)):
            ing.ingest("nonexistent_file.pdf")


# ── Article Ingestor Tests ───────────────────────────────────────────────────

class TestArticleIngestor:
    @patch("trafilatura.fetch_url")
    @patch("trafilatura.extract")
    def test_ingest_success(self, mock_extract, mock_fetch, sample_article_metadata):
        """Happy path: fetches and extracts article content."""
        mock_fetch.return_value = "<html><body><article>Content</article></body></html>"
        mock_extract.side_effect = [
            "Article body content here.",
            '{"title": "Test Article", "author": "Jane", "date": "2025-01-01"}',
        ]
        from app.ingestors.article import ArticleIngestor
        ing = ArticleIngestor()
        result = ing.ingest("https://example.com/article")
        assert "Article body content" in result["text"]

    @patch("trafilatura.fetch_url")
    def test_ingest_fetch_failure(self, mock_fetch):
        """When fetch_url fails, should propagate error."""
        mock_fetch.side_effect = Exception("Network error")
        from app.ingestors.article import ArticleIngestor
        ing = ArticleIngestor()
        with pytest.raises(Exception, match="Network error"):
            ing.ingest("https://example.com/article")

    def test_validate_http_urls(self):
        """validate() should accept http/https URLs."""
        from app.ingestors.article import ArticleIngestor
        ing = ArticleIngestor()
        assert ing.validate("https://example.com/article") is True
        assert ing.validate("http://blog.example.org/post.html") is True
        assert ing.validate("not-a-url") is False
        assert ing.validate("") is False

    @patch("trafilatura.fetch_url")
    @patch("trafilatura.extract")
    def test_extract_with_metadata(self, mock_extract, mock_fetch, sample_article_metadata):
        """Metadata should be parsed from JSON output."""
        mock_fetch.return_value = "<html><body>Content</body></html>"
        mock_extract.side_effect = [
            "Body text.",
            '{"title": "Test", "author": "Jane"}',
        ]
        from app.ingestors.article import ArticleIngestor
        ing = ArticleIngestor()
        result = ing.ingest("https://example.com/article")
        assert "metadata" in result
        assert isinstance(result["metadata"], dict)


# ── Audio Ingestor Tests ─────────────────────────────────────────────────────

class TestAudioIngestor:
    @patch("faster_whisper.WhisperModel")
    def test_ingest_success(self, mock_whisper):
        """Happy path: transcribes audio file successfully."""
        segment = MagicMock()
        segment.text = "Transcribed audio content."
        segment.start = 0.0
        segment.end = 5.0
        mock_whisper.return_value.transcribe.return_value = ([segment], "en")
        from app.ingestors.audio import AudioIngestor
        ing = AudioIngestor()
        result = ing.ingest("audio.mp3")
        assert result["title"] == "audio.mp3"
        assert "Transcribed audio" in result["text"]
        assert result["metadata"]["model"] == "base"
        assert result["metadata"]["language"] == "en"

    @patch("faster_whisper.WhisperModel")
    def test_transcription_segments_combined(self, mock_whisper):
        """Multiple transcription segments should be joined."""
        segments = []
        for i, (text, start, end) in enumerate([
            ("First segment.", 0.0, 3.0),
            ("Second segment.", 3.0, 6.0),
            ("Third and final.", 6.0, 9.0),
        ]):
            seg = MagicMock()
            seg.text = text
            seg.start = start
            seg.end = end
            segments.append(seg)
        mock_whisper.return_value.transcribe.return_value = (segments, "en")
        from app.ingestors.audio import AudioIngestor
        ing = AudioIngestor()
        result = ing.ingest("podcast.mp3")
        assert "First segment." in result["text"]
        assert "Second segment." in result["text"]
        assert "Third and final." in result["text"]

    def test_validate_audio_files(self):
        """validate() should accept common audio extensions."""
        from app.ingestors.audio import AudioIngestor
        ing = AudioIngestor()
        assert ing.validate("audio.mp3") is True
        assert ing.validate("recording.wav") is True
        assert ing.validate("podcast.m4a") is True
        assert ing.validate("speech.ogg") is True
        assert ing.validate("document.pdf") is False
        assert ing.validate("") is False

    def test_ingest_missing_file(self):
        """Should handle missing audio files gracefully."""
        from app.ingestors.audio import AudioIngestor
        ing = AudioIngestor()
        with pytest.raises((FileNotFoundError, Exception)):
            ing.ingest("nonexistent_audio.mp3")
