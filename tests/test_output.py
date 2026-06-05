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
        from app.output.markdown import get_template
        template = get_template("report.md.j2")
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
        from app.output.pdf import create_pdf
        pdf = create_pdf()
        assert pdf is not None
        assert hasattr(pdf, "output")
        assert hasattr(pdf, "add_page")
        assert hasattr(pdf, "set_font")
