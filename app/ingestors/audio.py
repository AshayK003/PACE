from pathlib import Path
from typing import Any

from app.config import ALLOWED_AUDIO_EXTENSIONS
from app.ingestors.base import BaseIngestor


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
