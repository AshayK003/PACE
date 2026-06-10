import json
import re
from typing import Any
from urllib.parse import urlparse, quote

import trafilatura

try:
    from curl_cffi import requests as curl_requests
    _HAS_CURL_CFFI = True
except Exception:
    import httpx as curl_requests  # type: ignore[no-redef]
    _HAS_CURL_CFFI = False

from app.ingestors.base import BaseIngestor
from app.security import is_safe_url


class ArticleIngestor(BaseIngestor):
    _REQUEST_KWARGS: dict[str, Any] = {"timeout": 15}
    _REDIRECT_KEY = "allow_redirects" if _HAS_CURL_CFFI else "follow_redirects"
    if _HAS_CURL_CFFI:
        _REQUEST_KWARGS["impersonate"] = "chrome"

    def validate(self, source: str) -> bool:
        if not source:
            return False
        try:
            result = urlparse(source)
            if result.scheme not in ("http", "https"):
                return False
            if not bool(result.netloc):
                return False
            if not is_safe_url(source):
                return False
            return True
        except Exception:
            return False

    def ingest(self, source: str) -> dict[str, Any]:
        if not is_safe_url(source):
            raise ValueError(f"URL is blocked for security reasons: {source}")

        text, html = self._fetch_and_extract(source)

        if not text or len(text.strip()) < 100:
            for fallback_fn in [
                self._try_wayback,
                self._try_archive_ph,
                self._try_google_cache,
            ]:
                try:
                    fb_text, fb_title = fallback_fn(source)
                    if fb_text and len(fb_text.strip()) > 100:
                        return {"title": fb_title or source, "text": fb_text, "metadata": {"source": "archive"}}
                except Exception:
                    continue

        if not text:
            raise ValueError(f"Could not fetch URL: {source}")

        title = self._extract_title(html) if html else ""
        return {"title": title or source, "text": text, "metadata": {}}

    def _fetch_and_extract(self, url: str) -> tuple[str, str]:
        try:
            resp = curl_requests.get(url, **self._REQUEST_KWARGS)
            if resp.status_code == 200 and len(resp.text) > 100:
                text = trafilatura.extract(resp.text, output_format="txt", include_links=True) or ""
                if text and len(text.strip()) > 100:
                    return text, resp.text
        except Exception:
            pass

        html = trafilatura.fetch_url(url)
        if not html:
            return "", ""
        text = trafilatura.extract(html, output_format="txt", include_links=True) or ""
        return text, html

    def _try_wayback(self, url: str) -> tuple[str, str]:
        api = f"https://archive.org/wayback/available?url={quote(url)}"
        resp = curl_requests.get(api, **self._REQUEST_KWARGS)
        if resp.status_code != 200:
            return "", ""
        data = resp.json()
        snapshot = data.get("archived_snapshots", {}).get("closest", {})
        if not snapshot or not snapshot.get("url"):
            return "", ""
        html = trafilatura.fetch_url(snapshot["url"])
        if not html:
            return "", ""
        text = trafilatura.extract(html, output_format="txt", include_links=True) or ""
        title = self._extract_title(html)
        return text, title

    def _try_archive_ph(self, url: str) -> tuple[str, str]:
        archive_url = f"https://archive.ph/newest/{url}"
        resp = curl_requests.get(archive_url, **{self._REDIRECT_KEY: True}, **self._REQUEST_KWARGS)
        if resp.status_code != 200:
            return "", ""
        text = trafilatura.extract(resp.text, output_format="txt", include_links=True) or ""
        title = self._extract_title(resp.text)
        return text, title

    def _try_google_cache(self, url: str) -> tuple[str, str]:
        cache_url = f"https://webcache.googleusercontent.com/search?q=cache:{url}"
        resp = curl_requests.get(cache_url, **{self._REDIRECT_KEY: True}, **self._REQUEST_KWARGS)
        if resp.status_code != 200:
            return "", ""
        text = trafilatura.extract(resp.text, output_format="txt", include_links=True) or ""
        title = self._extract_title(resp.text)
        return text, title

    def _extract_title(self, html: str) -> str:
        match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else ""
