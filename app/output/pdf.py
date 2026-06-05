from pathlib import Path

from fpdf import FPDF
from mistletoe import Document
from mistletoe.block_token import Heading, Paragraph, List, ListItem, CodeFence, Quote, ThematicBreak
from mistletoe.span_token import RawText

_FONTS_DIR = Path(__file__).parent / "fonts"
_NEEDED = ["DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans-Oblique.ttf", "DejaVuSans-BoldOblique.ttf"]
_FALLBACK_URLS = [
    "https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_2_37/dejavu-fonts-ttf-2.37.zip",
    "https://sourceforge.net/projects/dejavu/files/dejavu/2.37/dejavu-fonts-ttf-2.37.zip",
]

_MARGIN = 20
_CONTENT_W = 170
_LINE_H = 5.5
_BODY_SZ = 10
_H2_SZ = 14
_H3_SZ = 12
_CODE_SZ = 8.5
_SMALL_SZ = 8

_C_ACCENT = (27, 42, 74)
_C_ACCENT2 = (45, 74, 122)
_C_BODY = (44, 44, 44)
_C_MUTED = (136, 136, 136)
_C_CODE_BG = (245, 245, 245)
_C_QUOTE_BAR = (74, 144, 217)
_C_HR = (204, 204, 204)
_C_WHITE = (255, 255, 255)
_C_COVER_ACCENT = (32, 50, 88)


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
                    (_FONTS_DIR / fname).write_bytes(z.read(name))
            if all((_FONTS_DIR / f).exists() for f in _NEEDED):
                return True
        except Exception:
            continue
    return False


_fonts_loaded = False
_FONT = "Helvetica"


def _ensure_fonts() -> str:
    global _fonts_loaded, _FONT
    if _fonts_loaded:
        return _FONT
    if _load_fonts():
        _FONT = "DejaVu"
    _fonts_loaded = True
    return _FONT


class ReportPDF(FPDF):
    def __init__(self, title: str = "", source_type: str = "", source_url: str = "", date_analyzed: str = ""):
        super().__init__()
        self.report_title = title
        self.source_type = source_type
        self.source_url = source_url
        self.date_analyzed = date_analyzed
        self.set_margins(_MARGIN, 15, _MARGIN)
        self.set_auto_page_break(auto=True, margin=25)
        font = _ensure_fonts()
        if font == "DejaVu":
            for style, fname in [
                ("", "DejaVuSans.ttf"),
                ("B", "DejaVuSans-Bold.ttf"),
                ("I", "DejaVuSans-Oblique.ttf"),
                ("BI", "DejaVuSans-BoldOblique.ttf"),
            ]:
                self.add_font("DejaVu", style, str(_FONTS_DIR / fname))

    def footer(self):
        if self.page_no() > 1:
            self.set_y(-15)
            self.set_font(_FONT, size=_SMALL_SZ)
            self.set_text_color(*_C_MUTED)
            self.cell(0, 10, f"\u2014  {self.page_no()}  \u2014", align="C")


def _collect_text(node) -> str:
    children = getattr(node, "children", None)
    if children is None:
        return getattr(node, "content", "")
    parts = []
    for child in children:
        if isinstance(child, RawText):
            parts.append(child.content)
        else:
            parts.append(_collect_text(child))
    return "".join(parts)


def _strip_front_matter(md: str) -> str:
    lines = md.split("\n")
    for i, line in enumerate(lines):
        if line.strip() == "---":
            return "\n".join(lines[i + 1:])
    return md


def _cover_page(pdf: ReportPDF):
    pdf.add_page()
    w = pdf.w
    bar_h = 95

    pdf.set_fill_color(*_C_COVER_ACCENT)
    pdf.rect(0, 0, w, bar_h, "F")

    pdf.set_y(28)
    pdf.set_font(_FONT, "B", 22)
    pdf.set_text_color(*_C_WHITE)
    pdf.cell(0, 10, "ANALYSIS REPORT", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font(_FONT, size=10)
    pdf.cell(0, 7, "Precise Analysis and Compilation of Extracts", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(3)
    pdf.set_draw_color(255, 255, 255)
    pdf.set_line_width(0.5)
    y = pdf.get_y()
    pdf.line(65, y, w - 65, y)
    pdf.ln(6)

    pdf.set_font(_FONT, "B", 18)
    pdf.cell(0, 9, "PACE", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_y(bar_h + 20)
    pdf.set_font(_FONT, "B", _BODY_SZ)
    pdf.set_text_color(*_C_MUTED)
    pdf.cell(0, 7, "Report Details", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_draw_color(*_C_HR)
    pdf.set_line_width(0.3)
    y = pdf.get_y()
    pdf.line(70, y, w - 70, y)
    pdf.ln(8)

    pdf.set_text_color(*_C_BODY)
    rows = [
        ("Title", pdf.report_title),
        ("Source", pdf.source_type),
        ("URL", pdf.source_url) if pdf.source_url else None,
        ("Analyzed", pdf.date_analyzed),
    ]
    for row in rows:
        if row is None:
            continue
        label, value = row
        pdf.set_x(45)
        pdf.set_font(_FONT, "B", _BODY_SZ)
        pdf.cell(22, 7, label)
        pdf.set_font(_FONT, "", _BODY_SZ)
        pdf.cell(0, 7, value, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    pdf.ln(10)
    pdf.set_draw_color(*_C_HR)
    pdf.set_line_width(0.3)
    y = pdf.get_y()
    pdf.line(55, y, w - 55, y)
    pdf.ln(5)
    pdf.set_font(_FONT, size=_SMALL_SZ)
    pdf.set_text_color(*_C_MUTED)
    pdf.cell(0, 6, "Generated by PACE \u2014 AI-Powered Content Analysis System", align="C")


def _render_block(pdf: ReportPDF, node, level: int = 0):
    if node.children is None:
        return
    for child in node.children:
        if isinstance(child, Heading):
            _render_heading(pdf, child)
        elif isinstance(child, Paragraph):
            _render_paragraph(pdf, child, level)
        elif isinstance(child, List):
            _render_list(pdf, child, level)
        elif isinstance(child, CodeFence):
            _render_code(pdf, child)
        elif isinstance(child, Quote):
            _render_quote(pdf, child, level)
        elif isinstance(child, ThematicBreak):
            _render_hr(pdf)
        else:
            if child.children is not None:
                _render_block(pdf, child, level)


def _render_heading(pdf: ReportPDF, node: Heading):
    text = _collect_text(node).strip()
    if not text:
        return

    if node.level == 2:
        if pdf.get_y() > pdf.h - 25:
            pdf.add_page()
        pdf.ln(4)
        pdf.set_fill_color(*_C_ACCENT)
        pdf.set_text_color(*_C_WHITE)
        pdf.set_font(_FONT, "B", _H2_SZ)
        pdf.cell(_CONTENT_W, 8.5, f"  {text}", fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
    elif node.level == 3:
        pdf.ln(3)
        pdf.set_text_color(*_C_ACCENT2)
        pdf.set_font(_FONT, "B", _H3_SZ)
        pdf.cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")
        y = pdf.get_y()
        pdf.set_draw_color(*_C_ACCENT2)
        pdf.set_line_width(0.4)
        pdf.line(_MARGIN, y, _MARGIN + _CONTENT_W, y)
        pdf.ln(3)
    else:
        pdf.ln(2)
        pdf.set_font(_FONT, "B", _BODY_SZ)
        pdf.set_text_color(*_C_BODY)
        pdf.cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)


def _render_paragraph(pdf: ReportPDF, node: Paragraph, level: int = 0):
    text = _collect_text(node).strip()
    if not text:
        return
    if pdf.get_y() > pdf.h - 15:
        pdf.add_page()
    pdf.set_font(_FONT, "", _BODY_SZ)
    pdf.set_text_color(*_C_BODY)
    pdf.multi_cell(_CONTENT_W, _LINE_H, text)
    pdf.ln(2)


def _render_list(pdf: ReportPDF, node: List, level: int = 0):
    ordered = node.start is not None
    for i, item in enumerate(node.children):
        _render_list_item(pdf, item, level, ordered, i + 1)


def _render_list_item(pdf: ReportPDF, node: ListItem, level: int, ordered: bool, num: int):
    if pdf.get_y() > pdf.h - 18:
        pdf.add_page()
    text = _collect_text(node).strip()
    if text:
        prefix = f"{num}. " if ordered else "\u2022  "
        pdf.set_font(_FONT, "", _BODY_SZ)
        pdf.set_text_color(*_C_BODY)
        pdf.multi_cell(_CONTENT_W, _LINE_H, prefix + text)
        pdf.ln(1)

    for child in node.children:
        if isinstance(child, List):
            _render_list(pdf, child, level + 1)


def _render_code(pdf: ReportPDF, node: CodeFence):
    code_text = _collect_text(node)
    if not code_text.strip():
        return
    lines = code_text.rstrip("\n").split("\n")
    line_h = _CODE_SZ * 0.38 + 2
    total_h = max(len(lines), 1) * line_h + 5

    if pdf.get_y() > pdf.h - total_h - 15:
        pdf.add_page()
    pdf.ln(2)
    y_start = pdf.get_y()

    pdf.set_fill_color(*_C_CODE_BG)
    pdf.rect(_MARGIN, y_start, _CONTENT_W, total_h, "F")
    pdf.set_fill_color(*_C_ACCENT)
    pdf.rect(_MARGIN, y_start, 2.5, total_h, "F")

    pdf.set_font(_FONT, "", _CODE_SZ)
    pdf.set_text_color(*_C_BODY)
    y_pos = y_start + 2.5
    for line in lines:
        pdf.set_xy(_MARGIN + 6, y_pos)
        pdf.cell(_CONTENT_W - 12, line_h, line)
        y_pos += line_h

    pdf.set_y(y_start + total_h + 3)


def _render_quote(pdf: ReportPDF, node: Quote, level: int = 0):
    if pdf.get_y() > pdf.h - 20:
        pdf.add_page()
    pdf.ln(2)
    text = _collect_text(node).strip()
    if text:
        y_start = pdf.get_y()
        pdf.set_font(_FONT, "", _BODY_SZ)
        pdf.set_text_color(*_C_BODY)
        pdf.set_x(_MARGIN + 5)
        pdf.multi_cell(_CONTENT_W - 5, _LINE_H, text)
        y_end = pdf.get_y()
        pdf.set_fill_color(*_C_QUOTE_BAR)
        pdf.rect(_MARGIN, y_start - 1, 2.0, y_end - y_start + 2, "F")
    pdf.ln(3)


def _render_hr(pdf: ReportPDF):
    pdf.ln(3)
    y = pdf.get_y()
    pdf.set_draw_color(*_C_HR)
    pdf.set_line_width(0.3)
    pdf.line(_MARGIN, y, _MARGIN + _CONTENT_W, y)
    pdf.ln(4)


def _render_markdown_body(pdf: ReportPDF, md: str):
    body = _strip_front_matter(md)
    if not body.strip():
        pdf.set_font(_FONT, size=_BODY_SZ)
        pdf.set_text_color(*_C_MUTED)
        pdf.cell(0, 10, "No content.", align="C")
        return
    doc = Document(body)
    _render_block(pdf, doc)


def render_pdf(
    markdown_text: str,
    title: str = "",
    source_type: str = "",
    source_url: str = "",
    date_analyzed: str = "",
) -> bytes:
    pdf = ReportPDF(title=title, source_type=source_type, source_url=source_url, date_analyzed=date_analyzed)
    _cover_page(pdf)
    _render_markdown_body(pdf, markdown_text)
    return bytes(pdf.output())


def save_pdf(pdf_bytes: bytes, path: str | Path) -> None:
    Path(path).write_bytes(pdf_bytes)
