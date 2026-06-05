from pathlib import Path
from typing import Any

from fpdf import FPDF
from mistletoe import Document
from mistletoe.html_renderer import HTMLRenderer

_FONTS_DIR = Path(__file__).parent / "fonts"
_NEEDED = ["DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans-Oblique.ttf", "DejaVuSans-BoldOblique.ttf"]
_FALLBACK_URLS = [
    "https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_2_37/dejavu-fonts-ttf-2.37.zip",
    "https://sourceforge.net/projects/dejavu/files/dejavu/2.37/dejavu-fonts-ttf-2.37.zip",
]


def _load_fonts() -> bool:
    _FONTS_DIR.mkdir(parents=True, exist_ok=True)
    if all((_FONTS_DIR / f).exists() for f in _NEEDED):
        return True
    import io, zipfile, urllib.request
    for url in _FALLBACK_URLS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "PACE/1.0"})
            data = urllib.request.urlopen(req, timeout=30).read()
            z = zipfile.ZipFile(io.BytesIO(data))
            for name in z.namelist():
                fname = Path(name).name
                if fname in _NEEDED:
                    ( _FONTS_DIR / fname).write_bytes(z.read(name))
            if all((_FONTS_DIR / f).exists() for f in _NEEDED):
                return True
        except Exception:
            continue
    return False


_HAS_FONTS = _load_fonts()


def create_pdf() -> FPDF:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    if _HAS_FONTS:
        for style, fname in [("", "DejaVuSans.ttf"), ("B", "DejaVuSans-Bold.ttf"),
                             ("I", "DejaVuSans-Oblique.ttf"), ("BI", "DejaVuSans-BoldOblique.ttf")]:
            pdf.add_font("DejaVu", style, str(_FONTS_DIR / fname))
        pdf.set_font("DejaVu", size=11)
    else:
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
    return bytes(pdf.output())


def save_pdf(pdf_bytes: bytes, path: str | Path) -> None:
    Path(path).write_bytes(pdf_bytes)
