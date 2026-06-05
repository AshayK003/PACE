import os
from pathlib import Path
from typing import Any

from app.config import ALLOWED_AUDIO_EXTENSIONS
from app.ingestors.base import BaseIngestor

_CLOUD_ENV_VARS = {"STREAMLIT_CLOUD", "STREAMLIT_SHARING", "STREAMLIT_SERVER"}


def _is_cloud() -> bool:
    return bool(os.environ.get("STREAMLIT_CLOUD")) or any(
        v in os.environ for v in _CLOUD_ENV_VARS
    )


class AudioIngestor(BaseIngestor):
    def validate(self, source: str | Path) -> bool:
        if not source:
            return False
        ext = Path(str(source)).suffix.lower()
        return ext in ALLOWED_AUDIO_EXTENSIONS

    def ingest(self, source: str | Path) -> dict[str, Any]:
        source_path = Path(source)
        if not source_path.exists():
            raise FileNotFoundError(f"Audio file not found: {source}")
        if _is_cloud():
            return {
                "title": source_path.name,
                "text": "Audio transcription is not available in cloud environment. "
                        "Please run the analysis locally with ffmpeg installed.",
                "metadata": {
                    "model": "none",
                    "language": "unknown",
                    "segments": 0,
                    "cloud_fallback": True,
                },
            }
        import faster_whisper
        model = faster_whisper.WhisperModel("base", device="cpu", compute_type="int8")
        segments, info = model.transcribe(str(source_path))
        text_parts = []
        for segment in segments:
            text_parts.append(segment.text)
        text = " ".join(text_parts)
        language = "unknown"
        if info is not None:
            language = info.language if hasattr(info, "language") else str(info)
        return {
            "title": source_path.name,
            "text": text,
            "metadata": {
                "model": "base",
                "language": language,
                "segments": len(text_parts),
            },
        }
