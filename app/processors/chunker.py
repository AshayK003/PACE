from typing import Callable

import semchunk


def _default_token_counter(text: str) -> int:
    return len(text.split())


def chunk_text(
    text: str,
    chunk_size: int = 2000,
    overlap: int = 0,
    token_counter: Callable[[str], int] | None = None,
) -> list[str]:
    if not text:
        return []
    counter = token_counter or _default_token_counter
    if overlap > 0:
        chunks = _chunk_with_overlap(text, chunk_size, overlap, counter)
    else:
        chunks = semchunk.chunk(text, chunk_size, token_counter=counter)
    return chunks


def _chunk_with_overlap(
    text: str,
    chunk_size: int,
    overlap: int,
    token_counter: Callable[[str], int],
) -> list[str]:
    if len(text.split()) <= chunk_size:
        return [text]
    chunks = semchunk.chunk(text, chunk_size, token_counter=token_counter)
    if overlap <= 0 or len(chunks) <= 1:
        return chunks
    overlapped = []
    for i, chunk in enumerate(chunks):
        if i == 0:
            overlapped.append(chunk)
        else:
            prev_chunk = chunks[i - 1]
            words = prev_chunk.split()
            if len(words) > overlap:
                overlap_text = " ".join(words[-overlap:])
                overlapped.append(overlap_text + " " + chunk)
            else:
                overlapped.append(prev_chunk + " " + chunk)
    return overlapped
