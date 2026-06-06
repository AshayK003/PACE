from io import BytesIO

from ebooklib import epub
from mistletoe import Document, HTMLRenderer


_CSS = """
body { font-family: Georgia, serif; line-height: 1.6; margin: 2em; color: #2c3e50; }
h1 { color: #1a2a4a; border-bottom: 2px solid #1a2a4a; padding-bottom: 0.3em; }
h2 { color: #2d4a7a; margin-top: 1.5em; }
h3 { color: #2d4a7a; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; }
th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
th { background-color: #f2f2f2; font-weight: bold; }
code { background: #f5f5f5; padding: 2px 4px; border-radius: 3px; font-size: 0.9em; }
pre { background: #f5f5f5; padding: 12px; border-left: 3px solid #2d4a7a; overflow-x: auto; }
blockquote { border-left: 3px solid #4a90d9; margin-left: 0; padding-left: 1em; color: #555; }
hr { border: none; border-top: 1px solid #ccc; margin: 2em 0; }
"""


def render_epub(
    markdown_text: str,
    title: str = "PACE Report",
    author: str = "PACE",
) -> bytes:
    """Convert markdown content to EPUB binary.

    Uses mistletoe for markdown→HTML and ebooklib for EPUB packaging.
    Returns EPUB file as bytes.
    """
    book = epub.EpubBook()
    slug = title.lower().replace(" ", "-")[:50]
    book.set_identifier(f"pace-{slug}")
    book.set_title(title)
    book.set_language("en")
    book.add_author(author)

    css_item = epub.EpubItem(
        uid="style",
        file_name="style/default.css",
        media_type="text/css",
        content=_CSS.encode("utf-8"),
    )
    book.add_item(css_item)

    body = _strip_front_matter(markdown_text)
    renderer = HTMLRenderer()
    html_content = renderer.render(Document(body)) if body.strip() else "<p>No content.</p>"

    chapter = epub.EpubHtml(title=title, file_name="chapter1.xhtml", lang="en")
    chapter.content = html_content
    chapter.add_item(css_item)
    book.add_item(chapter)

    book.toc = [epub.Link("chapter1.xhtml", title, "ch1")]
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav", chapter]

    buf = BytesIO()
    epub.write_epub(buf, book, {})
    buf.seek(0)
    return buf.read()


def _strip_front_matter(md: str) -> str:
    lines = md.split("\n")
    for i, line in enumerate(lines):
        if line.strip() == "---":
            return "\n".join(lines[i + 1:])
    return md
