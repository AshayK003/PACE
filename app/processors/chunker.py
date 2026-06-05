from typing import Callable

import semchunk


def _default_token_counter(text: str) -> int:
    return len(text.split())


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
    chunks = semchunk.chunk(text, chunk_size, token_counter=counter)
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
        carry_tokens = 0
        for word in reversed(words):
            candidate = " ".join([word] + carry) if carry else word
            if token_counter(candidate) > overlap:
                break
            carry.insert(0, word)
            carry_tokens = token_counter(" ".join(carry))
        if carry:
            result.append(" ".join(carry) + " " + chunks[i])
        else:
            result.append(chunks[i])
    return result
