import re
from datetime import date


def render_obsidian(
    markdown_text: str,
    title: str = "PACE Report",
    source_type: str = "",
    source_url: str = "",
    date_analyzed: str = "",
    category: str = "",
    vault_path: str = "",
) -> str:
    """Wrap markdown report in YAML frontmatter for Obsidian compatibility.

    Adds tags, source metadata, and aliases so the file is searchable
    and linkable in an Obsidian vault.
    """
    tags = ["pace", "analysis"]
    if source_type:
        tags.append(source_type.lower())
    if category:
        for part in category.split("/"):
            cleaned = part.strip().lower()
            if cleaned and cleaned not in tags:
                tags.append(cleaned)

    frontmatter_lines = [
        "---",
        f"title: {_yaml_scalar(title)}",
        f"date: {date_analyzed or date.today().isoformat()}",
        f"source_type: {_yaml_scalar(source_type)}",
    ]
    if source_url:
        frontmatter_lines.append(f"source_url: {source_url}")
    if category:
        frontmatter_lines.append(f"category: {_yaml_scalar(category)}")
    frontmatter_lines.append(f"tags: [{', '.join(tags)}]")
    frontmatter_lines.append(f"aliases: [{_yaml_scalar(title)}]")
    if vault_path:
        frontmatter_lines.append(f"vault_path: {_yaml_scalar(vault_path)}")
    frontmatter_lines.append("---")
    frontmatter_lines.append("")

    body = _strip_existing_frontmatter(markdown_text)
    return "\n".join(frontmatter_lines) + body


def _yaml_scalar(value: str) -> str:
    """Wrap a string in quotes if it contains YAML-special characters."""
    if not value:
        return '""'
    if value.startswith(("http://", "https://")):
        return value
    if re.search(r"[:{}\[\],&*?|>!%@`#\-]", value) or value.startswith((" ", "'", '"')):
        return f'"{value}"'
    return value


def _strip_existing_frontmatter(md: str) -> str:
    lines = md.split("\n")
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return "\n".join(lines[i + 1:])
    return md
