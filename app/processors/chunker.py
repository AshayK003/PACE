from typing import Callable


def _default_token_counter(text: str) -> int:
    return len(text.split())


def _get_semchunk():
    """Lazy import of semchunk with graceful fallback."""
    try:
        import semchunk

        return semchunk
    except ImportError:

        def _simple_chunk(text: str, chunk_size: int) -> list[str]:
            """Fallback chunker when semchunk is not installed.

            Splits text on sentence boundaries to stay under chunk_size tokens.
            """
            words = text.split()
            chunks = []
            for i in range(0, len(words), chunk_size):
                chunks.append(" ".join(words[i : i + chunk_size]))
            return chunks

        return type("_SemchunkStub", (), {"chunk": staticmethod(_simple_chunk)})()


def chunk_text(
    text: str,
    chunk_size: int = 2000,
    overlap: int = 0,
    token_counter: Callable[[str], int] | None = None,
    max_chunks: int | None = None,
) -> list[str]:
    if not text:
        return []
    counter = token_counter or _default_token_counter
    chunker = _get_semchunk()
    chunks = chunker.chunk(text, chunk_size, token_counter=counter)
    if max_chunks is not None and len(chunks) > max_chunks:
        chunks = chunks[:max_chunks]
    if overlap > 0 and len(chunks) > 1:
        chunks = _add_overlap(chunks, overlap, counter)
    return chunks


def _add_overlap(
    chunks: list[str],
    overlap: int,
    token_counter: Callable[[str], int],
) -> list[str]:
    result = [chunks[0]]
    for i in range(1, len(chunks)):
        prev = chunks[i - 1]
        words = prev.split()
        carry = []
        for word in reversed(words):
            candidate = " ".join([word] + carry) if carry else word
            if token_counter(candidate) > overlap:
                break
            carry.insert(0, word)
        if carry:
            result.append(" ".join(carry) + " " + chunks[i])
        else:
            result.append(chunks[i])
    return result
