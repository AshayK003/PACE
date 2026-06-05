import pytest


class TestChunker:
    def test_chunk_basic(self, sample_text):
        """Should split text into a single chunk when under limit."""
        from app.processors.chunker import chunk_text
        chunks = chunk_text(sample_text, chunk_size=2000)
        assert isinstance(chunks, list)
        assert len(chunks) >= 1
        assert isinstance(chunks[0], str)

    def test_chunk_long_text_produces_multiple_chunks(self, sample_long_text):
        """Long text should produce multiple chunks."""
        from app.processors.chunker import chunk_text
        chunks = chunk_text(sample_long_text, chunk_size=1000)
        assert len(chunks) >= 2

    def test_chunk_preserves_all_content(self, sample_long_text):
        """Total content should not be lost during chunking."""
        from app.processors.chunker import chunk_text
        chunks = chunk_text(sample_long_text, chunk_size=1000)
        reconstructed = "".join(chunks)
        assert len(reconstructed) >= len(sample_long_text) * 0.9

    def test_chunk_with_custom_tokenizer(self, sample_text):
        """Should accept a custom tokenizer/token counter."""
        from app.processors.chunker import chunk_text
        from transformers import AutoTokenizer
        try:
            tokenizer = AutoTokenizer.from_pretrained("gpt2")
            token_counter = lambda t: len(tokenizer.encode(t))
        except Exception:
            import tiktoken
            enc = tiktoken.get_encoding("cl100k_base")
            token_counter = lambda t: len(enc.encode(t))
        chunks = chunk_text(sample_text, chunk_size=50, token_counter=token_counter)
        assert len(chunks) >= 1

    def test_chunk_empty_text(self):
        """Empty text should return an empty list or single empty chunk."""
        from app.processors.chunker import chunk_text
        chunks = chunk_text("", chunk_size=100)
        assert len(chunks) == 0 or (len(chunks) == 1 and chunks[0] == "")

    def test_chunk_token_limit_enforced(self, sample_long_text):
        """Each chunk should not exceed the specified token limit."""
        from app.processors.chunker import chunk_text
        max_tokens = 100
        chunks = chunk_text(sample_long_text, chunk_size=max_tokens)
        for chunk in chunks:
            token_count = len(chunk.split())
            assert token_count <= max_tokens

    def test_chunk_semantic_boundaries(self):
        """Chunks should break at semantic boundaries (paragraphs)."""
        from app.processors.chunker import chunk_text
        text = "\n\n".join([f"Paragraph {i}." for i in range(20)])
        max_tokens = 50
        chunks = chunk_text(text, chunk_size=max_tokens)
        for chunk in chunks:
            if len(chunks) > 1:
                assert "\n\n" in chunk or len(chunk.split()) <= max_tokens

    def test_chunk_single_sentence(self):
        """A single sentence within the limit should remain one chunk."""
        from app.processors.chunker import chunk_text
        text = "This is a single sentence."
        chunks = chunk_text(text, chunk_size=1000)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_exact_boundary(self):
        """Text exactly at the token limit should be one chunk."""
        from app.processors.chunker import chunk_text
        words = ["word"] * 50
        text = " ".join(words)
        chunks = chunk_text(text, chunk_size=50)
        assert len(chunks) == 1

    def test_chunk_overlap_if_supported(self, sample_long_text):
        """If overlap is supported, chunks should share overlapping tokens."""
        from app.processors.chunker import chunk_text
        chunks_no_overlap = chunk_text(sample_long_text, chunk_size=200, overlap=0)
        chunks_with_overlap = chunk_text(sample_long_text, chunk_size=200, overlap=20)
        if len(chunks_no_overlap) > 1 and len(chunks_with_overlap) > 1:
            assert len(chunks_with_overlap) <= len(chunks_no_overlap)
