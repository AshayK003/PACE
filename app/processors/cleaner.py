import re

FILLER_WORDS = {
    "um", "uh", "like", "basically", "you know",
    "i mean", "sort of", "kind of", "so", "well", "literally",
    "honestly", "essentially", "virtually",
}


def remove_fillers(text: str) -> str:
    if not text:
        return text
    pattern = re.compile(
        r"\b(?:" + "|".join(re.escape(w) for w in FILLER_WORDS) + r")\b[,]?\s*",
        re.IGNORECASE,
    )
    return pattern.sub("", text)


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
    pattern = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\s*", re.MULTILINE)
    return pattern.sub("", text)


def remove_urls(text: str) -> str:
    if not text:
        return text
    pattern = re.compile(r"https?://\S+")
    return pattern.sub("", text)


def clean_pipeline(text: str) -> str:
    if not text:
        return ""
    text = remove_urls(text)
    text = remove_timestamps(text)
    text = remove_fillers(text)
    text = deduplicate_lines(text)
    text = normalize_whitespace(text)
    return text.strip()
