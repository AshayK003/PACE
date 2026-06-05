import re
from typing import Any

import youtube_transcript_api

from app.ingestors.base import BaseIngestor


class YouTubeIngestor(BaseIngestor):
    def validate(self, source: str) -> bool:
        if not source:
            return False
        patterns = [
            r"youtube\.com/watch\?",
            r"youtu\.be/",
            r"m\.youtube\.com/watch\?",
        ]
        return any(re.search(p, source) for p in patterns)

    def _extract_video_id(self, url: str) -> str | None:
        if not url:
            return None
        patterns = [
            r"(?:youtube\.com/watch\?.*v=)([\w-]+)",
            r"(?:youtu\.be/)([\w-]+)",
            r"(?:m\.youtube\.com/watch\?.*v=)([\w-]+)",
        ]
        for pattern in patterns:
            m = re.search(pattern, url)
            if m:
                return m.group(1)
        return None

    def ingest(self, source: str) -> dict[str, Any]:
        video_id = self._extract_video_id(source)
        if not video_id:
            raise ValueError(f"Could not extract video ID from: {source}")
        transcript = youtube_transcript_api.YouTubeTranscriptApi().fetch(video_id)
        text = " ".join(segment["text"] for segment in transcript)
        return {
            "title": f"YouTube Video ({video_id})",
            "text": text,
            "metadata": {
                "video_id": video_id,
                "source": "transcript",
                "segments": len(transcript),
            },
        }
