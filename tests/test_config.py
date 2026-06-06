import pytest


class TestSafeFilename:
    @pytest.mark.parametrize("title,expected_prefix_or_exact", [
        ("The Future of AI in Healthcare", "the_future_of_ai"),
        ("   My   Title   ", "my_title"),
        ("", "report"),
        ("!!!@@@###", "report"),
        ("A" * 100, "a" * 60),
        ("中文標題測試", "中文標題測試"),
        ("Hello-World_Test", "hello_world_test"),
        ("Trailing --- underscores ___ ", "trailing"),
        ("Smartly—Formatted–Title", "smartlyformattedtitle"),
        ("nopath/nope", "nopathnope"),
    ])
    def test_edge_cases(self, title, expected_prefix_or_exact):
        from app.config import safe_filename
        result = safe_filename(title)
        assert result
        if len(expected_prefix_or_exact) <= 60 and result == expected_prefix_or_exact:
            pass
        else:
            assert result.startswith(expected_prefix_or_exact), f"{result!r} does not start with {expected_prefix_or_exact!r}"

    @pytest.mark.parametrize("title,expected", [
        ("a" * 60, "a" * 60),
        ("a" * 61, "a" * 60),
        ("hello", "hello"),
    ])
    def test_length_limits(self, title, expected):
        from app.config import safe_filename
        assert safe_filename(title) == expected

    def test_max_len_param(self):
        from app.config import safe_filename
        assert len(safe_filename("hello world", max_len=5)) <= 5
        assert safe_filename("hello world", max_len=50) == "hello_world"


class TestApiKey:
    def test_get_api_key_from_env(self):
        from app.config import get_api_key
        import os
        os.environ["OPENCODE_ZEN_KEY"] = "env-key-123"
        try:
            assert get_api_key() == "env-key-123"
        finally:
            os.environ["OPENCODE_ZEN_KEY"] = ""

    def test_get_api_key_returns_empty_when_not_set(self):
        from app.config import get_api_key
        import os
        os.environ.pop("OPENCODE_ZEN_KEY", None)
        result = get_api_key()
        assert result == "" or result is None


class TestSourceType:
    def test_source_type_values(self):
        from app.config import SourceType
        assert SourceType.YOUTUBE.value == "YouTube"
        assert SourceType.PDF.value == "PDF"
        assert SourceType.ARTICLE.value == "Article"
        assert SourceType.AUDIO.value == "Audio"
        assert SourceType.TEXT.value == "Text"

    def test_source_type_from_value(self):
        from app.config import SourceType
        assert SourceType("YouTube") == SourceType.YOUTUBE
        assert SourceType("PDF") == SourceType.PDF
        assert SourceType("Text") == SourceType.TEXT


class TestBuildExportPath:
    def test_basic_path(self):
        from app.config import build_export_path
        result = build_export_path("Tech", "AI", "transformer_explained", "2026-06-06")
        assert result["folder"] == "Tech/AI"
        assert result["filename"] == "2026-06-06_transformer_explained"
        assert result["full_path"] == "Tech/AI/2026-06-06_transformer_explained"

    def test_invalid_domain_defaults_to_other(self):
        from app.config import build_export_path
        result = build_export_path("InvalidDomain", "Sub", "slug", "2026-01-01")
        assert result["folder"] == "Other/Sub"

    def test_empty_sub_topic_defaults_to_unsorted(self):
        from app.config import build_export_path
        result = build_export_path("Tech", "", "slug", "2026-01-01")
        assert result["folder"] == "Tech/Unsorted"

    def test_empty_slug_defaults_to_report(self):
        from app.config import build_export_path
        result = build_export_path("Tech", "AI", "", "2026-01-01")
        assert result["filename"] == "2026-01-01_report"

    def test_special_chars_stripped(self):
        from app.config import build_export_path
        result = build_export_path("Finance", "Crypto & Blockchain", "btc@2026!", "2026-06-06")
        assert "Crypto" in result["folder"]
        assert "&" not in result["folder"]
        assert "@" not in result["filename"]
        assert "!" not in result["filename"]

    def test_all_valid_domains(self):
        from app.config import build_export_path
        for domain in ["Tech", "Business", "Science", "Health", "Education", "Culture", "Finance", "Politics", "Sports", "Other"]:
            result = build_export_path(domain, "Sub", "slug", "2026-01-01")
            assert result["folder"].startswith(domain + "/")
