import json
from typing import Any
from urllib.parse import urlparse

import trafilatura

from app.ingestors.base import BaseIngestor


class ArticleIngestor(BaseIngestor):
    def validate(self, source: str) -> bool:
        if not source:
            return False
        try:
            result = urlparse(source)
            return result.scheme in ("http", "https") and bool(result.netloc)
        except Exception:
            return False

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
        title = metadata.get("title", "")
        if not title:
            title = source
        return {
            "title": title,
            "text": text,
            "metadata": metadata,
        }
