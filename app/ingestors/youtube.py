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
            r"youtube\.com/embed/",
            r"youtube\.com/shorts/",
            r"youtube\.com/live/",
        ]
        return any(re.search(p, source) for p in patterns)

    def _extract_video_id(self, url: str) -> str | None:
        if not url:
            return None
        patterns = [
            r"(?:youtube\.com/watch\?.*v=)([\w-]+)",
            r"(?:youtu\.be/)([\w-]+)",
            r"(?:m\.youtube\.com/watch\?.*v=)([\w-]+)",
            r"(?:youtube\.com/embed/)([\w-]+)",
            r"(?:youtube\.com/shorts/)([\w-]+)",
            r"(?:youtube\.com/live/)([\w-]+)",
        ]
        for pattern in patterns:
            m = re.search(pattern, url)
            if m:
                return m.group(1)
        return None

    @staticmethod
    def _get_segment_text(segment: Any) -> str:
        if isinstance(segment, dict):
            return segment.get("text", "")
        return getattr(segment, "text", "")

    def ingest(self, source: str) -> dict[str, Any]:
        video_id = self._extract_video_id(source)
        if not video_id:
            raise ValueError(f"Could not extract video ID from: {source}")
        api = youtube_transcript_api.YouTubeTranscriptApi()
        language_codes = ["en", "en-GB", "en-US", "hi", "auto"]
        transcript = None
        language_used = "en"
        for lang in language_codes:
            try:
                transcript = api.fetch(video_id, languages=[lang])
                language_used = lang
                break
            except Exception:
                continue
        if transcript is None:
            try:
                transcript_list = api.list(video_id)
                best = None
                try:
                    best = transcript_list.find_manually_created_transcript(["en", "hi", "en-GB"])
                except Exception:
                    pass
                if best is None:
                    try:
                        best = transcript_list.find_generated_transcript(["en", "hi", "en-GB"])
                    except Exception:
                        pass
                if best is None:
                    available = [str(t) for t in transcript_list]
                    raise ValueError(
                        f"No suitable transcript found for {video_id}. "
                        f"Available: {', '.join(available) if available else 'none'}"
                    )
                transcript = best.fetch()
                language_used = best.language
            except youtube_transcript_api.NoTranscriptFound:
                raise ValueError(f"No transcript available for video {video_id}")
        segments = list(transcript)
        text = " ".join(self._get_segment_text(seg) for seg in segments)
        return {
            "title": f"YouTube Video ({video_id})",
            "text": text,
            "metadata": {
                "video_id": video_id,
                "source": "transcript",
                "language": language_used,
                "segments": len(segments),
            },
        }
