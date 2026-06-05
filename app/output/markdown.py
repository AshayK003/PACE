from pathlib import Path
from typing import Any

from jinja2 import Template

TEMPLATES_DIR = Path(__file__).parent / "templates"

_REPORT_TEMPLATE = Template(TEMPLATES_DIR.joinpath("report.md.j2").read_text(encoding="utf-8"))
_EXECUTIVE_TEMPLATE = Template(TEMPLATES_DIR.joinpath("executive.md.j2").read_text(encoding="utf-8"))

_LIST_SECTIONS = {"key_takeaways", "frameworks", "action_items", "risks", "notable_quotes"}


def _to_list(value: Any) -> Any:
    if isinstance(value, list):
        return value
    if not isinstance(value, str):
        return []
    lines = [line.strip("- *").strip() for line in value.strip().split("\n")]
    return [line for line in lines if line]


def _normalize(data: dict[str, Any]) -> dict[str, Any]:
    result = dict(data)
    for key in _LIST_SECTIONS:
        result[key] = _to_list(result.get(key))
    return result


def render_markdown(data: dict[str, Any]) -> str:
    return _REPORT_TEMPLATE.render(**_normalize(data))


def render_executive(data: dict[str, Any]) -> str:
    return _EXECUTIVE_TEMPLATE.render(**_normalize(data))


def save_markdown(content: str, path: str | Path) -> None:
    Path(path).write_text(content, encoding="utf-8")
