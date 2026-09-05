"""Shared output helpers (single source of truth for report rendering)."""


def strip_front_matter(md: str) -> str:
    """Remove a leading ---...--- front-matter block, if present.

    Only strips when the document OPENS with --- through a closing ---.
    A mid-document thematic break must never delete content.
    """
    lines = md.split("\n")
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return "\n".join(lines[i + 1:])
    return md
