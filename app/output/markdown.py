from datetime import date
from pathlib import Path
from typing import Any

from jinja2 import Template

TEMPLATES_DIR = Path(__file__).parent / "templates"


def get_template(name: str) -> Template:
    path = TEMPLATES_DIR / name
    return Template(path.read_text(encoding="utf-8"))


def render_markdown(data: dict[str, Any]) -> str:
    template = get_template("report.md.j2")
    return template.render(**data)


def render_executive(data: dict[str, Any]) -> str:
    template = get_template("executive.md.j2")
    return template.render(**data)


def save_markdown(content: str, path: str | Path) -> None:
    Path(path).write_text(content, encoding="utf-8")
