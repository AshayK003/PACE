import os
import re
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

ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".wma"}


def get_api_key() -> str:
    key = os.environ.get("OPENCODE_ZEN_KEY", "")
    if not key:
        try:
            key = st.secrets.get("OPENCODE_ZEN_KEY", "")
        except (FileNotFoundError, ValueError):
            pass
    return key


def safe_filename(title: str, max_len: int = 60) -> str:
    name = re.sub(r"[^\w\s-]", "", title).strip().lower()
    name = re.sub(r"[-\s]+", "_", name)
    name = name.strip("_")
    if not name:
        return "report"
    if len(name) > max_len:
        name = name[:max_len].rstrip("_")
    return name


_DOMAINS = {
    "Tech", "Business", "Science", "Health", "Education",
    "Culture", "Finance", "Politics", "Sports", "Other",
}


def build_export_path(
    domain: str,
    sub_topic: str,
    slug: str,
    date_str: str,
) -> dict:
    if domain not in _DOMAINS:
        domain = "Other"
    sub_topic = re.sub(r"[^a-zA-Z0-9\s_-]", "", sub_topic).strip() or "Unsorted"
    sub_topic = re.sub(r"\s+", "_", sub_topic)
    slug = re.sub(r"[^a-z0-9_-]", "", slug.lower().strip()) or "report"

    folder = f"{domain}/{sub_topic}"
    filename = f"{date_str}_{slug}"
    full_path = f"{folder}/{filename}"
    return {"folder": folder, "filename": filename, "full_path": full_path}
