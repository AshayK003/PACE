from pathlib import Path
from typing import Any

from fpdf import FPDF
from mistletoe import Document
from mistletoe.html_renderer import HTMLRenderer


def create_pdf() -> FPDF:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    return pdf


def markdown_to_pdf_content(pdf: FPDF, markdown_text: str) -> None:
    if not markdown_text.strip():
        pdf.cell(0, 10, "No content to display.")
        return
    renderer = HTMLRenderer()
    html = renderer.render(Document(markdown_text))
    html = html.replace("<h1>", '<h1 style="font-size:18pt;margin-top:10px;">')
    html = html.replace("<h2>", '<h2 style="font-size:14pt;margin-top:8px;">')
    html = html.replace("<h3>", '<h3 style="font-size:12pt;margin-top:6px;">')
    full_html = f"<html><body>{html}</body></html>"
    pdf.add_page()
    pdf.write_html(full_html)


def render_pdf(markdown_text: str) -> bytes:
    pdf = create_pdf()
    markdown_to_pdf_content(pdf, markdown_text)
    return bytes(pdf.output(dest="S"))


def save_pdf(pdf_bytes: bytes, path: str | Path) -> None:
    Path(path).write_bytes(pdf_bytes)
