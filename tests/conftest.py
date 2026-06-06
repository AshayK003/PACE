import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(autouse=True)
def _create_dummy_audio_files():
    dummy_files = ["audio.mp3", "podcast.mp3"]
    for fname in dummy_files:
        Path(fname).touch()
    yield
    for fname in dummy_files:
        Path(fname).unlink(missing_ok=True)


# ── Sample Content Fixtures ──────────────────────────────────────────────────

@pytest.fixture
def sample_text() -> str:
    return """Artificial intelligence is transforming how we process information.

The key insight is that context matters more than raw data volume. When analyzing
long-form content, understanding the structure and relationships between ideas is
more important than capturing every word.

Research shows that chunking content into semantic units improves comprehension
by up to 40%. This is why semantic chunking outperforms simple character-splitting."""


@pytest.fixture
def sample_long_text() -> str:
    paragraphs = []
    for i in range(50):
        paragraphs.append(
            f"Paragraph {i + 1}. This is a sample paragraph containing enough text "
            "to test chunking behavior across multiple semantic units. "
            "It has multiple sentences to ensure proper boundary detection. "
            "We need enough content here to trigger multi-chunk splits."
        )
    return "\n\n".join(paragraphs)


@pytest.fixture
def sample_transcript() -> list[dict]:
    return [
        {"text": "Welcome to this presentation on machine learning.", "duration": 3.0, "offset": 0},
        {"text": "Today we will cover three main concepts.", "duration": 4.0, "offset": 3.0},
        {"text": "First, supervised learning techniques.", "duration": 5.0, "offset": 7.0},
        {"text": "Second, unsupervised learning approaches.", "duration": 5.0, "offset": 12.0},
        {"text": "And third, reinforcement learning fundamentals.", "duration": 6.0, "offset": 17.0},
    ]


@pytest.fixture
def sample_text_with_fillers() -> str:
    return (
        "So, um, basically the thing is that, you know, like, "
        "we need to actually consider the, uh, implications of this approach. "
        "I mean, honestly, it's kind of a, sort of, game-changing methodology."
    )


@pytest.fixture
def sample_text_with_timestamps() -> str:
    return (
        "00:00 Welcome to the presentation.\n"
        "01:30 First, let's discuss the problem.\n"
        "03:45 Next, we examine solutions.\n"
        "06:20 Finally, the conclusion.\n"
    )


@pytest.fixture
def sample_text_with_duplicates() -> str:
    return (
        "This is a unique line.\n"
        "This is a repeated line.\n"
        "This is another unique line.\n"
        "This is a repeated line.\n"
        "This is a unique line again.\n"
        "This is a repeated line.\n"
    )


@pytest.fixture
def sample_article_metadata() -> dict:
    return {
        "title": "The Future of AI Summarization",
        "author": "Jane Doe",
        "date": "2025-06-01",
        "site": "TechJournal",
        "categories": ["AI", "NLP"],
    }


@pytest.fixture
def sample_report_data() -> dict:
    return {
        "title": "Analysis of: The Future of AI",
        "source_type": "YouTube",
        "source_url": "https://youtube.com/watch?v=example",
        "date_analyzed": "2025-06-05",
        "executive_summary": "This video presents a comprehensive overview of AI summarization.",
        "key_takeaways": [
            "Context matters more than data volume",
            "Semantic chunking improves comprehension by 40%",
        ],
        "detailed_analysis": "The speaker covers three main areas...",
        "supporting_evidence": "Studies show semantic chunking outperforms...",
        "frameworks": ["Semantic Chunking", "Hierarchical Analysis"],
        "action_items": ["Implement chunking", "Use semantic splitting"],
        "risks": ["Over-chunking can lose context", "Quality depends on source"],
        "notable_quotes": ["\"Context is king\" - Speaker"],
        "missing_but_important": ["Cost implications not addressed", "Scalability concerns missing"],
        "final_synthesis": "AI summarization is evolving rapidly...",
    }


@pytest.fixture
def mock_llm_response():
    """Mock an OpenAI chat completions response."""
    mock = MagicMock()
    mock.choices = [MagicMock()]
    mock.choices[0].message.content = "This is a mock LLM analysis response."
    mock.usage = MagicMock()
    mock.usage.prompt_tokens = 100
    mock.usage.completion_tokens = 50
    mock.usage.total_tokens = 150
    return mock


# ── Temp Directory Fixtures ──────────────────────────────────────────────────

@pytest.fixture
def temp_output_dir() -> Path:
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def temp_pdf_path(temp_output_dir) -> Path:
    return temp_output_dir / "test_report.pdf"


@pytest.fixture
def temp_md_path(temp_output_dir) -> Path:
    return temp_output_dir / "test_report.md"


# ── Config Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def set_env_vars():
    old_key = os.environ.get("OPENCODE_ZEN_KEY", "")
    os.environ["OPENCODE_ZEN_KEY"] = "test-key"
    yield
    os.environ["OPENCODE_ZEN_KEY"] = old_key
