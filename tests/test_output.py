import pytest
from pathlib import Path


# ── Markdown Rendering Tests ─────────────────────────────────────────────────

class TestMarkdownRenderer:
    def test_render_full_report(self, sample_report_data):
        """Full report should render all 10 sections."""
        from app.output.markdown import render_markdown
        output = render_markdown(sample_report_data)
        assert isinstance(output, str)
        assert len(output) > 100

    def test_render_contains_title(self, sample_report_data):
        """Report should include the title."""
        from app.output.markdown import render_markdown
        output = render_markdown(sample_report_data)
        assert sample_report_data["title"] in output

    def test_render_contains_section_headings(self, sample_report_data):
        """All major sections should be present as headings."""
        from app.output.markdown import render_markdown
        output = render_markdown(sample_report_data)
        section_keywords = [
            "Executive Summary",
            "Key Takeaways",
            "Detailed Analysis",
            "Supporting Evidence",
            "Frameworks",
            "Action Items",
            "Risks",
            "Notable Quotes",
            "Missing",
            "Final Synthesis",
        ]
        for keyword in section_keywords:
            assert keyword in output, f"Missing section: {keyword}"

    def test_render_key_takeaways_as_list(self, sample_report_data):
        """Key takeaways should render as a bullet list."""
        from app.output.markdown import render_markdown
        output = render_markdown(sample_report_data)
        for takeaway in sample_report_data["key_takeaways"]:
            assert takeaway in output

    def test_render_action_items_as_list(self, sample_report_data):
        """Action items should render as a bullet or checklist."""
        from app.output.markdown import render_markdown
        output = render_markdown(sample_report_data)
        for item in sample_report_data["action_items"]:
            assert item in output

    def test_render_risk_items(self, sample_report_data):
        """Risks should be included in output."""
        from app.output.markdown import render_markdown
        output = render_markdown(sample_report_data)
        for risk in sample_report_data["risks"]:
            assert risk in output

    def test_render_frameworks_list(self, sample_report_data):
        """Frameworks should appear in the rendered output."""
        from app.output.markdown import render_markdown
        output = render_markdown(sample_report_data)
        for framework in sample_report_data["frameworks"]:
            assert framework in output

    def test_render_executive_summary_only(self, sample_report_data):
        """Executive summary template should render only summary sections."""
        from app.output.markdown import render_executive, render_markdown
        output = render_executive(sample_report_data)
        assert isinstance(output, str)
        assert len(output) > 20
        assert len(output) < len(render_markdown(sample_report_data))

    def test_render_handles_empty_sections(self):
        """Rendering should handle empty or missing sections gracefully."""
        from app.output.markdown import render_markdown
        empty_data = {
            "title": "Test",
            "source_type": "Text",
            "source_url": "",
            "date_analyzed": "2025-01-01",
            "executive_summary": "",
            "key_takeaways": [],
            "detailed_analysis": "",
            "supporting_evidence": "",
            "frameworks": [],
            "action_items": [],
            "risks": [],
            "notable_quotes": [],
            "missing_but_important": "",
            "final_synthesis": "",
        }
        output = render_markdown(empty_data)
        assert isinstance(output, str)
        assert "Test" in output

    def test_render_with_special_characters(self, sample_report_data):
        """Special characters (quotes, dashes, etc.) should render correctly."""
        from app.output.markdown import render_markdown
        sample_report_data["notable_quotes"] = [
            "\"Quote with special chars: — – … © ® ™\""
        ]
        output = render_markdown(sample_report_data)
        assert "Quote with special chars" in output

    def test_render_content_saves_to_file(self, sample_report_data, temp_md_path):
        """Rendered markdown should save to a file correctly."""
        from app.output.markdown import render_markdown, save_markdown
        content = render_markdown(sample_report_data)
        save_markdown(content, temp_md_path)
        assert temp_md_path.exists()
        saved_content = temp_md_path.read_text(encoding="utf-8")
        assert saved_content == content

    def test_jinja2_template_loads(self):
        """The Jinja2 template should load without errors."""
        from app.output.markdown import _REPORT_TEMPLATE
        template = _REPORT_TEMPLATE
        assert template is not None
        rendered = template.render(title="Test")
        assert "Test" in rendered


# ── PDF Generation Tests ─────────────────────────────────────────────────────

class TestPDFRenderer:
    def test_generate_pdf_from_markdown(self, sample_report_data):
        """Should generate PDF bytes from markdown content."""
        from app.output.markdown import render_markdown
        from app.output.pdf import render_pdf
        md_content = render_markdown(sample_report_data)
        pdf_bytes = render_pdf(md_content)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 100

    def test_pdf_starts_with_pdf_magic_bytes(self, sample_report_data):
        """Generated PDF should start with %PDF magic bytes."""
        from app.output.markdown import render_markdown
        from app.output.pdf import render_pdf
        md_content = render_markdown(sample_report_data)
        pdf_bytes = render_pdf(md_content)
        assert pdf_bytes[:5] == b"%PDF-"

    def test_pdf_contains_visible_text(self, sample_report_data):
        """PDF should contain text from the markdown content."""
        from app.output.markdown import render_markdown
        from app.output.pdf import render_pdf
        md_content = render_markdown(sample_report_data)
        pdf_bytes = render_pdf(md_content)
        assert pdf_bytes[:5] == b"%PDF-"
        assert len(pdf_bytes) > 500

    def test_pdf_with_empty_content(self):
        """Empty markdown should produce a minimal valid PDF."""
        from app.output.pdf import render_pdf
        pdf_bytes = render_pdf("")
        assert pdf_bytes[:5] == b"%PDF-"
        assert len(pdf_bytes) >= 100

    def test_pdf_preserves_headings(self):
        """Markdown headings should appear in the PDF."""
        from app.output.pdf import render_pdf
        md = "# Title\n\n## Section 1\n\nContent here.\n\n## Section 2\n\nMore content."
        pdf_bytes = render_pdf(md)
        assert pdf_bytes[:5] == b"%PDF-"

    def test_pdf_with_tables(self):
        """Markdown tables should render as tables in PDF."""
        from app.output.pdf import render_pdf
        md = "| Col1 | Col2 |\n|------|------|\n| A    | B    |\n| C    | D    |"
        pdf_bytes = render_pdf(md)
        assert pdf_bytes[:5] == b"%PDF-"

    def test_pdf_with_lists(self):
        """Markdown lists should render in PDF."""
        from app.output.pdf import render_pdf
        md = "- Item 1\n- Item 2\n- Item 3"
        pdf_bytes = render_pdf(md)
        assert pdf_bytes[:5] == b"%PDF-"

    def test_pdf_saves_to_file(self, sample_report_data, temp_pdf_path):
        """PDF bytes should save to a file correctly."""
        from app.output.markdown import render_markdown
        from app.output.pdf import render_pdf, save_pdf
        md_content = render_markdown(sample_report_data)
        pdf_bytes = render_pdf(md_content)
        save_pdf(pdf_bytes, temp_pdf_path)
        assert temp_pdf_path.exists()
        assert temp_pdf_path.stat().st_size > 100

    def test_pdf_streamlit_download_compatible(self, sample_report_data):
        """Output should be compatible with Streamlit's download_button."""
        from app.output.markdown import render_markdown
        from app.output.pdf import render_pdf
        md_content = render_markdown(sample_report_data)
        pdf_bytes = render_pdf(md_content)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

    def test_pdf_with_unicode_characters(self):
        """Unicode characters should render in PDF."""
        from app.output.pdf import render_pdf
        md = "# Análise\n\n## Résumé\n\nContenido con acentos: áéíóú ñ ü"
        pdf_bytes = render_pdf(md)
        assert pdf_bytes[:5] == b"%PDF-"

    def test_pdf_with_code_blocks(self):
        """Code blocks should be handled in PDF."""
        from app.output.pdf import render_pdf
        md = "```python\nprint('hello')\n```"
        pdf_bytes = render_pdf(md)
        assert pdf_bytes[:5] == b"%PDF-"

    def test_pdf_with_links(self):
        """Links should be included in PDF output."""
        from app.output.pdf import render_pdf
        md = "[OpenAI](https://openai.com)"
        pdf_bytes = render_pdf(md)
        assert pdf_bytes[:5] == b"%PDF-"

    def test_pdf_default_configuration(self):
        """PDF generation should use sensible defaults (A4, portrait, mm)."""
        from app.output.pdf import ReportPDF
        pdf = ReportPDF()
        assert pdf is not None
        assert hasattr(pdf, "output")
        assert hasattr(pdf, "add_page")
        assert hasattr(pdf, "set_font")

    def test_pdf_full_report_with_metadata(self):
        """Full report markdown with metadata, tables, code, quotes renders safely."""
        from app.output.pdf import render_pdf
        md = (
            "# Test Analysis\n\n"
            "**Source:** YouTube | https://youtube.com/watch?v=abc\n"
            "**Analyzed:** 2026-06-05\n\n"
            "---\n\n"
            "## Executive Summary\n\n"
            "This is a **bold** and *italic* test with `inline code`.\n\n"
            "## Key Takeaways\n\n"
            "- First item with **bold**\n"
            "- Second item with *italic*\n"
            "- Third item with `code`\n\n"
            "## Code Example\n\n"
            "```python\n"
            "def hello():\n"
            '    print("world")\n'
            "```\n\n"
            "## Quote Example\n\n"
            "> This is a **blockquote** with *formatting*\n\n"
            "## Table Test\n\n"
            "| A | B |\n"
            "|---|---|\n"
            "| 1 | 2 |\n\n"
            "---\n\n"
            "## Final\n\n"
            "Normal paragraph with a [link](https://example.com)."
        )
        pdf_bytes = render_pdf(md)
        assert pdf_bytes[:5] == b"%PDF-"
        assert len(pdf_bytes) > 1000

    def test_pdf_renders_actual_text_content(self):
        """Generated PDF should contain readable text when extracted."""
        from app.output.pdf import render_pdf
        import fitz
        md = "# Title\n\n## Section One\n\nVisible text content here.\n\n## Section Two\n\nMore visible text."
        pdf_bytes = render_pdf(md)
        doc = fitz.open("pdf", pdf_bytes)
        text = "".join(page.get_text() for page in doc)
        doc.close()
        assert "Section One" in text
        assert "Section Two" in text
        assert "Visible text content" in text

    def test_pdf_renders_bold_and_italic_text(self):
        """Bold and italic markdown should produce text content in PDF."""
        from app.output.pdf import render_pdf
        import fitz
        md = "# Styling\n\n**Bold text** and *italic text* and `inline code`."
        pdf_bytes = render_pdf(md)
        doc = fitz.open("pdf", pdf_bytes)
        text = "".join(page.get_text() for page in doc)
        doc.close()
        assert "Bold text" in text
        assert "italic text" in text
        assert "inline code" in text

    def test_pdf_renders_list_items(self):
        """Markdown lists should render their text in PDF."""
        from app.output.pdf import render_pdf
        import fitz
        md = "# List Test\n\n- First item\n- Second item\n- Third item"
        pdf_bytes = render_pdf(md)
        doc = fitz.open("pdf", pdf_bytes)
        text = "".join(page.get_text() for page in doc)
        doc.close()
        assert "First item" in text
        assert "Second item" in text
        assert "Third item" in text

    def test_pdf_renders_code_block(self):
        """Code blocks should render their content in PDF."""
        from app.output.pdf import render_pdf
        import fitz
        md = "```python\ndef hello():\n    print('world')\n```"
        pdf_bytes = render_pdf(md)
        doc = fitz.open("pdf", pdf_bytes)
        text = "".join(page.get_text() for page in doc)
        doc.close()
        assert "hello" in text
        assert "print" in text

    def test_pdf_cover_page_shows_title(self):
        """PDF cover page should include the report title."""
        from app.output.pdf import render_pdf
        import fitz
        md = "# Custom Report Title\n\n---\n\nContent."
        pdf_bytes = render_pdf(md, title="Custom Report Title")
        doc = fitz.open("pdf", pdf_bytes)
        text = "".join(page.get_text() for page in doc)
        doc.close()
        assert "Custom Report Title" in text

    @pytest.mark.parametrize("md,expected_section", [
        ("## Executive Summary\n\nContent.", "Executive Summary"),
        ("## Key Takeaways\n\nContent.", "Key Takeaways"),
        ("## Risks & Limitations\n\nContent.", "Risks & Limitations"),
    ])
    def test_pdf_preserves_section_headings(self, md, expected_section):
        """Section H2 headings should appear in rendered PDF."""
        from app.output.pdf import render_pdf
        import fitz
        pdf_bytes = render_pdf(md)
        doc = fitz.open("pdf", pdf_bytes)
        text = "".join(page.get_text() for page in doc)
        doc.close()
        assert expected_section in text

    @pytest.mark.parametrize("md,expected_stripped", [
        ("# Title\n\n---\n\nBody", "Body"),
        ("No separator here", "No separator here"),
        ("---\n\nSecond ---\n\nBody", "Second"),
        ("", ""),
        ("# Only metadata\n\n---", ""),
    ])
    def test_strip_front_matter(self, md, expected_stripped):
        """Front matter before first --- should be stripped."""
        from app.output.pdf import _strip_front_matter
        result = _strip_front_matter(md).strip()
        if expected_stripped:
            assert result.startswith(expected_stripped)
        else:
            assert not result


# ── EPUB Rendering Tests ─────────────────────────────────────────────────────

class TestEPUBRenderer:
    def test_render_epub_returns_bytes(self):
        from app.output.epub import render_epub
        result = render_epub("# Title\n\nBody text here.")
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_epub_starts_with_zip_magic(self):
        from app.output.epub import render_epub
        result = render_epub("# Title\n\nBody text here.")
        assert result[:2] == b"PK"

    def test_epub_contains_title(self):
        from app.output.epub import render_epub
        import zipfile
        result = render_epub("# My Report\n\nContent.", title="My Report")
        with zipfile.ZipFile(__import__("io").BytesIO(result)) as zf:
            names = zf.namelist()
            assert any("chapter1.xhtml" in n for n in names)
            content_opf = zf.read("EPUB/content.opf").decode()
            assert "My Report" in content_opf

    def test_epub_with_empty_content(self):
        from app.output.epub import render_epub
        result = render_epub("")
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_epub_with_tables(self):
        from app.output.epub import render_epub
        md = "# Title\n\n| Col A | Col B |\n|-------|-------|\n| 1 | 2 |"
        result = render_epub(md)
        assert isinstance(result, bytes)

    def test_epub_with_unicode(self):
        from app.output.epub import render_epub
        md = "# 中文标题\n\nÜnïcödé content with émojis 🎉"
        result = render_epub(md)
        assert isinstance(result, bytes)

    def test_epub_with_code_blocks(self):
        from app.output.epub import render_epub
        md = "# Title\n\n```python\nprint('hello')\n```"
        result = render_epub(md)
        assert isinstance(result, bytes)

    def test_epub_strips_front_matter(self):
        from app.output.epub import render_epub
        import zipfile
        md = "---\ntitle: Skipped\n---\n\n# Actual Title\n\nBody content."
        result = render_epub(md, title="Test")
        with zipfile.ZipFile(__import__("io").BytesIO(result)) as zf:
            chapter = zf.read("EPUB/chapter1.xhtml").decode()
            assert "Actual Title" in chapter
            content_opf = zf.read("EPUB/content.opf").decode()
            assert "Skipped" not in content_opf

    def test_epub_saves_to_file(self, temp_output_dir):
        from app.output.epub import render_epub
        result = render_epub("# Title\n\nContent.")
        path = temp_output_dir / "test.epub"
        path.write_bytes(result)
        assert path.exists()
        assert path.stat().st_size > 0


# ── Obsidian Rendering Tests ─────────────────────────────────────────────────

class TestObsidianRenderer:
    def test_render_obsidian_has_frontmatter(self):
        from app.output.obsidian import render_obsidian
        result = render_obsidian("# Report\n\nBody.", title="Report")
        assert result.startswith("---\n")
        assert result.count("---") >= 2

    def test_obsidian_contains_title(self):
        from app.output.obsidian import render_obsidian
        result = render_obsidian("# Report\n\nBody.", title="My Analysis")
        assert "title: My Analysis" in result

    def test_obsidian_contains_tags(self):
        from app.output.obsidian import render_obsidian
        result = render_obsidian("# Report\n\nBody.", title="Report", source_type="YouTube")
        assert "tags:" in result
        assert "pace" in result
        assert "youtube" in result

    def test_obsidian_contains_source_url(self):
        from app.output.obsidian import render_obsidian
        result = render_obsidian(
            "# Report\n\nBody.",
            title="Report",
            source_url="https://example.com/article",
        )
        assert "source_url: https://example.com/article" in result

    def test_obsidian_contains_date(self):
        from app.output.obsidian import render_obsidian
        result = render_obsidian(
            "# Report\n\nBody.",
            title="Report",
            date_analyzed="2025-06-05",
        )
        assert "date: 2025-06-05" in result

    def test_obsidian_aliases(self):
        from app.output.obsidian import render_obsidian
        result = render_obsidian("# Report\n\nBody.", title="My Report")
        assert "aliases:" in result
        assert "My Report" in result

    def test_obsidian_strips_existing_frontmatter(self):
        from app.output.obsidian import render_obsidian
        md = "---\ntitle: old\n---\n\n# New Title\n\nBody."
        result = render_obsidian(md, title="New Title")
        assert "title: New Title" in result
        assert "title: old" not in result

    def test_obsidian_yaml_special_chars(self):
        from app.output.obsidian import render_obsidian
        result = render_obsidian("# Report\n\nBody.", title="Report: A {Test}")
        assert 'title: "Report: A {Test}"' in result

    def test_obsidian_with_empty_content(self):
        from app.output.obsidian import render_obsidian
        result = render_obsidian("", title="Empty")
        assert result.startswith("---\n")

    def test_obsidian_preserves_body(self):
        from app.output.obsidian import render_obsidian
        body = "# Report\n\nThis is the analysis body."
        result = render_obsidian(body, title="Report")
        assert "This is the analysis body." in result

    def test_obsidian_contains_category(self):
        from app.output.obsidian import render_obsidian
        result = render_obsidian(
            "# Report\n\nBody.", title="Report", category="Tech/AI",
        )
        assert "category: Tech/AI" in result

    def test_obsidian_contains_vault_path(self):
        from app.output.obsidian import render_obsidian
        result = render_obsidian(
            "# Report\n\nBody.", title="Report",
            vault_path="Tech/AI/2026-06-06_report.md",
        )
        assert "vault_path:" in result
        assert "Tech/AI/2026-06-06_report.md" in result

    def test_obsidian_enriches_tags_with_category(self):
        from app.output.obsidian import render_obsidian
        result = render_obsidian(
            "# Report\n\nBody.", title="Report",
            source_type="YouTube", category="Tech/AI",
        )
        assert "tech" in result
        assert "ai" in result

    def test_obsidian_no_category_no_vault_path(self):
        from app.output.obsidian import render_obsidian
        result = render_obsidian("# Report\n\nBody.", title="Report")
        assert "category:" not in result
        assert "vault_path:" not in result
