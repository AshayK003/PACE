import os
from enum import Enum

import streamlit as st


class SourceType(str, Enum):
    YOUTUBE = "YouTube"
    PDF = "PDF"
    ARTICLE = "Article"
    AUDIO = "Audio"
    TEXT = "Text"


MODEL_NAME = "deepseek-v4-flash-free"
BASE_URL = "https://opencode.ai/zen/v1"

CHUNK_SIZE = 2000
CHUNK_OVERLAP = 100
MAX_TOKENS_PER_CHUNK = 2000

OUTPUT_SECTIONS = [
    "executive_summary",
    "key_takeaways",
    "detailed_analysis",
    "supporting_evidence",
    "frameworks",
    "action_items",
    "risks",
    "notable_quotes",
    "missing_but_important",
    "final_synthesis",
]

ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".wma"}

YOUTUBE_URL_PATTERNS = [
    "youtube.com/watch?",
    "youtu.be/",
    "www.youtube.com/watch?",
    "m.youtube.com/watch?",
]


def get_api_key() -> str:
    key = os.environ.get("OPENCODE_ZEN_KEY", "")
    if not key:
        try:
            key = st.secrets.get("OPENCODE_ZEN_KEY", "")
        except (FileNotFoundError, ValueError):
            pass
    return key
