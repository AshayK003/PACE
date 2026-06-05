import re
from typing import Any

_SECTION_DELIMITER = re.compile(r"^===([A-Z_]+)===$", re.MULTILINE)


def parse_batched_response(response: str, expected_sections: list[str]) -> dict[str, str]:
    sections: dict[str, str] = {}
    parts = _SECTION_DELIMITER.split(response)

    i = 1
    while i < len(parts) - 1:
        key = parts[i].strip().lower()
        content = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if key in expected_sections:
            sections[key] = content
        i += 2

    for section in expected_sections:
        if section not in sections:
            sections[section] = ""

    return sections


def batch_a_response(response: str) -> dict[str, str]:
    return parse_batched_response(response, ["executive_summary", "key_takeaways"])


def batch_b_response(response: str) -> dict[str, str]:
    return parse_batched_response(response, ["detailed_analysis", "supporting_evidence"])


def batch_c_response(response: str) -> dict[str, str]:
    return parse_batched_response(response, ["frameworks", "action_items", "risks", "notable_quotes"])
