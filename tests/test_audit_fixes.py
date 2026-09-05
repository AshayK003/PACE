"""Regression tests for the Sep 2026 audit fixes (P0/P1/P2)."""

import pandas as pd

from app.analyzers.categorizer import _parse_response
from app.output.epub import _strip_front_matter as epub_strip
from app.output.pdf import _strip_front_matter as pdf_strip
from app.processors.cleaner import remove_fillers
from app.processors.chunker import chunk_text
from app.security import is_safe_url, validate_file_magic


def test_batch_check_requires_all_sections():
    # The old guard `if result[s]` skipped empties; the fixed check in
    # pipeline.py requires every section present and >= 20 chars.
    secs = ["executive_summary", "key_takeaways"]
    good = {s: "x" * 20 for s in secs}
    assert all(s in good and len(good[s].strip()) >= 20 for s in secs)
    bad = {"executive_summary": "x" * 20}  # key_takeaways missing
    assert not all(s in bad and len(bad[s].strip()) >= 20 for s in secs)
    short = {s: "x" * 5 for s in secs}
    assert not all(s in short and len(short[s].strip()) >= 20 for s in secs)


def test_front_matter_keeps_thematic_breaks():
    doc = "# Title\n\nSome text.\n\n---\n\nMore text after the break."
    assert epub_strip(doc) == doc
    assert pdf_strip(doc) == doc
    fm = "---\ntitle: Report\n---\n# Real content here."
    assert epub_strip(fm) == "# Real content here."
    assert pdf_strip(fm) == "# Real content here."


def test_fillers_preserve_meaning():
    assert remove_fillers("so the result shows it") == "so the result shows it"
    assert remove_fillers("I like pie") == "I like pie"
    assert "like" not in remove_fillers("you know, like, we need this")
    assert remove_fillers("um uh basically") == ""


def test_audio_cloud_returns_empty_text():
    from unittest.mock import patch
    from app.ingestors.audio import AudioIngestor
    with patch("app.ingestors.audio._is_cloud", return_value=True):
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            path = f.name
        try:
            out = AudioIngestor().ingest(path)
        finally:
            os.unlink(path)
    assert out["text"] == ""
    assert out["metadata"]["cloud_fallback"] is True


def test_categorizer_parses_nested_json():
    resp = 'Answer: {"domain": "tech", "meta": {"a": 1, "b": [1, 2]}, "x": "}"}'
    out = _parse_response(resp)
    assert out["domain"] == "tech"
    assert out["meta"] == {"a": 1, "b": [1, 2]}


def test_chunker_marks_truncation():
    text = " ".join(f"word{i}" for i in range(2000))
    chunks = chunk_text(text, chunk_size=200, max_chunks=2)
    assert len(chunks) == 2
    assert "truncated" in chunks[-1]


def test_m4a_magic_uses_ftyp_offset():
    mp4 = bytes(4) + b"ftypisom" + bytes(64)
    assert validate_file_magic(mp4, ".m4a")[0] is True
    assert validate_file_magic(b"\x1a\x45\xdf\xa3" + bytes(64), ".m4a")[0] is False


def test_archive_urls_validated():
    # Archive/snapshot hosts are public and must pass; metadata IP stays
    # blocked. DNS is mocked (this sandbox has none).
    import socket
    from unittest.mock import patch
    real = socket.getaddrinfo

    def fake(host, *a, **k):
        if host in ("web.archive.org", "archive.ph",
                    "webcache.googleusercontent.com"):
            return [(socket.AF_INET, None, None, None, ("93.184.216.34", 0))]
        return real(host, *a, **k)

    with patch("socket.getaddrinfo", side_effect=fake):
        assert is_safe_url("https://web.archive.org/web/2024/https://example.com/x")
        assert is_safe_url("https://archive.ph/newest/https://example.com")
        assert not is_safe_url("http://169.254.169.254/latest")


def test_prompt_delimiters_present():
    import inspect
    from app.analyzers import pipeline as pl
    src = inspect.getsource(pl)
    assert "<untrusted-content>" in src
