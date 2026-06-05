from pathlib import Path
from typing import Any

from app.ingestors.base import BaseIngestor


class PDFIngestor(BaseIngestor):
    def validate(self, source: str | Path) -> bool:
        if not source:
            return False
        source_str = str(source)
        return source_str.lower().endswith(".pdf")

    def ingest(self, source: str | Path) -> dict[str, Any]:
        source_path = Path(source)
        text = ""
        tables = []
        parser_used = "pymupdf4llm"
        fallback_used = False
        try:
            import pymupdf4llm
            text = pymupdf4llm.to_markdown(str(source_path))
        except Exception:
            parser_used = "pypdf"
            fallback_used = True
            try:
                import pypdf
                reader = pypdf.PdfReader(str(source_path))
                text_parts = []
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                text = "\n\n".join(text_parts)
            except Exception:
                pass
        if not text:
            raise FileNotFoundError(f"Could not extract content from: {source}")
        try:
            import pdfplumber
            with pdfplumber.open(str(source_path)) as pdf:
                for page in pdf.pages:
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)
        except Exception:
            pass
        result: dict[str, Any] = {
            "title": source_path.name,
            "text": text,
            "metadata": {
                "parser": parser_used,
                "fallback_used": fallback_used,
            },
        }
        if tables:
            result["metadata"]["tables"] = tables
            result["metadata"]["tables_supplemented"] = True
        else:
            result["metadata"]["tables_supplemented"] = False
        return result
