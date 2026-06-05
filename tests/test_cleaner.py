import pytest


class TestCleaner:
    def test_remove_filler_words(self, sample_text_with_fillers):
        """Should remove common filler words from text."""
        from app.processors.cleaner import remove_fillers
        cleaned = remove_fillers(sample_text_with_fillers)
        assert "um" not in cleaned.lower()
        assert "uh" not in cleaned.lower()
        assert "like" not in cleaned.lower()
        assert "basically" not in cleaned.lower()
        assert "actually" in cleaned.lower()

    def test_remove_fillers_preserves_content(self, sample_text_with_fillers):
        """Removing fillers should not remove meaningful content words."""
        from app.processors.cleaner import remove_fillers
        cleaned = remove_fillers(sample_text_with_fillers)
        assert "consider" in cleaned
        assert "implications" in cleaned
        assert "game-changing" in cleaned
        assert "methodology" in cleaned

    def test_deduplicate_lines(self, sample_text_with_duplicates):
        """Should remove duplicate consecutive lines."""
        from app.processors.cleaner import deduplicate_lines
        cleaned = deduplicate_lines(sample_text_with_duplicates)
        lines = cleaned.strip().split("\n")
        unique_lines = set(lines)
        assert len(lines) <= len(sample_text_with_duplicates.strip().split("\n"))
        assert "This is a repeated line." in lines

    def test_deduplicate_preserves_order(self):
        """Deduplication should preserve first occurrence order."""
        from app.processors.cleaner import deduplicate_lines
        text = "A\nB\nC\nA\nD\nB\n"
        cleaned = deduplicate_lines(text)
        lines = cleaned.strip().split("\n")
        assert lines[0] == "A"
        assert lines[1] == "B"
        assert lines[2] == "C"
        assert lines[3] == "D"

    def test_normalize_whitespace(self):
        """Should collapse multiple spaces and trim."""
        from app.processors.cleaner import normalize_whitespace
        text = "  This   has  extra   spaces.  "
        cleaned = normalize_whitespace(text)
        assert cleaned == "This has extra spaces."

    def test_normalize_whitespace_preserves_newlines(self):
        """Newlines should not be removed by whitespace normalization."""
        from app.processors.cleaner import normalize_whitespace
        text = "Line 1.\n\nLine 2.\n\n\nLine 3."
        cleaned = normalize_whitespace(text)
        assert "\n" in cleaned

    def test_remove_timestamps(self, sample_text_with_timestamps):
        """Should remove common timestamp patterns."""
        from app.processors.cleaner import remove_timestamps
        cleaned = remove_timestamps(sample_text_with_timestamps)
        assert "00:00" not in cleaned
        assert "01:30" not in cleaned
        assert "03:45" not in cleaned
        assert "06:20" not in cleaned
        assert "Welcome to the presentation" in cleaned
        assert "discuss the problem" in cleaned

    def test_remove_timestamps_preserves_text(self, sample_text_with_timestamps):
        """Removing timestamps should not remove the text that follows."""
        from app.processors.cleaner import remove_timestamps
        cleaned = remove_timestamps(sample_text_with_timestamps)
        assert "presentation" in cleaned
        assert "problem" in cleaned
        assert "solutions" in cleaned
        assert "conclusion" in cleaned

    def test_clean_pipeline(self, sample_text_with_fillers):
        """Full cleaning pipeline should run all steps."""
        from app.processors.cleaner import clean_pipeline
        cleaned = clean_pipeline(sample_text_with_fillers)
        assert isinstance(cleaned, str)
        assert len(cleaned) > 0
        assert len(cleaned) <= len(sample_text_with_fillers)

    def test_clean_empty_input(self):
        """Empty input should not crash."""
        from app.processors.cleaner import clean_pipeline
        assert clean_pipeline("") == ""
        assert clean_pipeline("   ") == ""

    def test_clean_preserves_meaning(self):
        """Cleaning should preserve the core meaning of text."""
        from app.processors.cleaner import clean_pipeline
        text = "So, basically, the key finding is that AI improves efficiency."
        cleaned = clean_pipeline(text)
        assert "key finding" in cleaned
        assert "AI" in cleaned
        assert "efficiency" in cleaned

    def test_remove_urls(self):
        """URLs should be removed from text."""
        from app.processors.cleaner import remove_urls
        text = "Visit https://example.com or http://test.org/page?q=1 for more."
        cleaned = remove_urls(text)
        assert "https://example.com" not in cleaned
        assert "http://test.org/page?q=1" not in cleaned
        assert "Visit" in cleaned
        assert "for more" in cleaned

    def test_remove_special_characters(self):
        """Excessive special characters should be handled."""
        from app.processors.cleaner import clean_pipeline
        text = "Hello!!! *** What?? ## Yes!!!"
        cleaned = clean_pipeline(text)
        assert cleaned is not None
        assert "Hello" in cleaned

    @pytest.mark.parametrize("input_text,expected_terms", [
        ("Emoji test 🔥🚀 is cool", ["Emoji", "test", "cool"]),
        ("Café résumé über naïve", ["Café", "résumé", "über", "naïve"]),
        ("中文測試 日本語 확인", ["中文測試", "日本語", "확인"]),
        ("Hello\n\n\n\n\nWorld", ["Hello", "World"]),
        ("So, um, basically hello", ["hello"]),
    ])
    def test_cleaner_with_unicode_and_varied_inputs(self, input_text, expected_terms):
        """Cleaner should handle emoji, CJK, accented chars, and fillers."""
        from app.processors.cleaner import clean_pipeline
        result = clean_pipeline(input_text)
        for term in expected_terms:
            assert term in result, f"Expected {term!r} in {result!r}"

    def test_cleaner_removes_urls(self):
        """URLs should be stripped while surrounding text is preserved."""
        from app.processors.cleaner import clean_pipeline
        text = "Visit https://example.com/page?q=test&ref=1 for details."
        result = clean_pipeline(text)
        assert "https://" not in result
        assert "Visit" in result
        assert "details" in result

    def test_cleaner_with_only_fillers(self):
        """Text consisting entirely of filler words should become empty."""
        from app.processors.cleaner import clean_pipeline
        assert clean_pipeline("um uh like basically you know") == ""

    def test_cleaner_with_mixed_timestamps_and_fillers(self):
        """Timestamps and fillers should both be removed."""
        from app.processors.cleaner import clean_pipeline
        text = "00:15 So, um, basically the result was positive. 01:30 And, like, we saw improvement."
        result = clean_pipeline(text)
        assert "00:15" not in result
        assert "um" not in result
        assert "result was positive" in result
        assert "saw improvement" in result
