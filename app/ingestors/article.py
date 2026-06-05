import json
from typing import Any

import trafilatura

from app.ingestors.base import BaseIngestor


class ArticleIngestor(BaseIngestor):
    def validate(self, source: str) -> bool:
        if not source:
            return False
        return source.lower().startswith(("http://", "https://"))

    def ingest(self, source: str) -> dict[str, Any]:
        html = trafilatura.fetch_url(source)
        if html is None:
            raise ValueError(f"Could not fetch URL: {source}")
        text = trafilatura.extract(html, output_format="txt", include_links=True)
        if text is None:
            raise ValueError(f"Could not extract content from: {source}")
        metadata_str = trafilatura.extract(html, output_format="json", include_links=True)
        metadata: dict[str, Any] = {}
        if metadata_str:
            try:
                metadata = json.loads(metadata_str)
            except (json.JSONDecodeError, TypeError):
                pass
        return {
            "title": metadata.get("title", source),
            "text": text,
            "metadata": metadata,
        }
