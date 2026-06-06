import re
from typing import Pattern

FILLER_WORDS = {
    "um", "uh", "like", "basically", "you know",
    "i mean", "sort of", "kind of", "so", "well", "literally",
    "honestly", "essentially", "virtually",
}


def _build_filler_pattern() -> Pattern:
    words = sorted(FILLER_WORDS, key=len, reverse=True)
    return re.compile(
        r"\b(?:" + "|".join(re.escape(w) for w in words) + r")[,]?\s*",
        re.IGNORECASE,
    )


_FILLER_PATTERN = _build_filler_pattern()
_REPEATED_PUNCT_PATTERN = re.compile(r"[,]{2,}\s*[,]*")
_MULTI_SPACE_PATTERN = re.compile(r"[ \t]{2,}")
_TIMESTAMP_PATTERN = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\s*", re.MULTILINE)
_URL_PATTERN = re.compile(r"https?://\S+")


def remove_fillers(text: str) -> str:
    if not text:
        return text
    result = _FILLER_PATTERN.sub("", text)
    result = _REPEATED_PUNCT_PATTERN.sub(", ", result)
    result = _MULTI_SPACE_PATTERN.sub(" ", result)
    result = result.replace(", ,", ",").replace("  ,", " ").replace(",  ", ", ")
    result = result.strip().strip(",").strip()
    return result


def deduplicate_lines(text: str) -> str:
    if not text:
        return text
    seen = set()
    result = []
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped not in seen:
            seen.add(stripped)
            result.append(line)
    return "\n".join(result)


def normalize_whitespace(text: str) -> str:
    if not text:
        return ""
    lines = text.split("\n")
    normalized = []
    for line in lines:
        cleaned = re.sub(r"[ \t]+", " ", line).strip()
        normalized.append(cleaned)
    result = "\n".join(normalized)
    return result.strip()


def remove_timestamps(text: str) -> str:
    if not text:
        return text
    return _TIMESTAMP_PATTERN.sub("", text)


def remove_urls(text: str) -> str:
    if not text:
        return text
    return _URL_PATTERN.sub("", text)


def clean_pipeline(text: str) -> str:
    if not text:
        return ""
    text = remove_urls(text)
    text = remove_timestamps(text)
    text = remove_fillers(text)
    text = deduplicate_lines(text)
    text = normalize_whitespace(text)
    return text.strip()
