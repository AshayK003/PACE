import json
import re

from app.analyzers.llm_client import LLMClient

_VALID_DOMAINS = {
    "tech", "business", "science", "health", "education",
    "culture", "finance", "politics", "sports", "other",
}

_CATEGORIZATION_SYSTEM = (
    "You are a content categorizer. Given a title, key takeaways, and topic, "
    "return a JSON object with exactly three keys: "
    '"domain" (one of: Tech, Business, Science, Health, Education, Culture, '
    'Finance, Politics, Sports, Other), '
    '"sub_topic" (max 2 words, snake_case), and '
    '"slug" (max 5 words, snake_case, no special characters). '
    "Return ONLY the JSON object, no explanation."
)

_FALLBACK = {"domain": "Other", "sub_topic": "Unsorted", "slug": "report"}


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s_-]", "", text)
    text = re.sub(r"[\s-]+", "_", text)
    text = text.strip("_")
    words = text.split("_")[:5]
    return "_".join(words) if words else "report"


def categorize_content(
    client: LLMClient,
    title: str,
    key_takeaways: list[str],
    topic: str,
) -> dict:
    takeaways_text = "\n".join(f"- {t}" for t in key_takeaways[:5]) if key_takeaways else "(none)"
    user_message = (
        f"Title: {title}\n"
        f"Topic: {topic}\n"
        f"Key Takeaways:\n{takeaways_text}"
    )

    try:
        response = client.send(
            system_prompt=_CATEGORIZATION_SYSTEM,
            user_message=user_message,
            temperature=0.1,
            max_tokens=100,
        )
        result = _parse_response(response)
        return _validate_result(result)
    except Exception:
        return dict(_FALLBACK)


def _parse_response(response: str) -> dict:
    match = re.search(r"\{[^}]+\}", response)
    if not match:
        return dict(_FALLBACK)
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return dict(_FALLBACK)


def _validate_result(result: dict) -> dict:
    domain = str(result.get("domain", "")).strip()
    if domain.lower() not in _VALID_DOMAINS:
        domain = "Other"

    sub_topic = str(result.get("sub_topic", "Unsorted")).strip()[:40]
    sub_topic = re.sub(r"[^a-zA-Z0-9\s_-]", "", sub_topic)
    sub_topic = re.sub(r"[\s]+", "_", sub_topic).strip("_") or "Unsorted"

    slug = str(result.get("slug", "report")).strip()[:60]
    slug = _slugify(slug) or "report"

    return {"domain": domain, "sub_topic": sub_topic, "slug": slug}
