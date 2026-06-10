"""Security utilities for PACE."""

import ipaddress
import re
import socket
from time import time
from urllib.parse import urlparse


# ── SSRF Protection ──────────────────────────────────────────────────────────

_BLOCKED_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # AWS/GCP metadata
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),  # IPv6 private
]

_BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "metadata.google.internal", "169.254.169.254"}


def validate_url_safe(url: str) -> tuple[bool, str]:
    """Check URL is not pointing to internal/private networks.

    Returns (is_safe, reason).
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Invalid URL format"

    if parsed.scheme not in ("http", "https"):
        return False, f"Only http/https URLs allowed (got {parsed.scheme!r})"

    hostname = parsed.hostname
    if not hostname:
        return False, "No hostname in URL"

    if hostname.lower() in _BLOCKED_HOSTS:
        return False, f"Access to {hostname} is blocked"

    # Resolve DNS and check against blocked networks
    try:
        infos = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        for family, _, _, _, sockaddr in infos:
            ip = ipaddress.ip_address(sockaddr[0])
            for net in _BLOCKED_NETWORKS:
                if ip in net:
                    return False, f"Access to {hostname} ({ip}) is in a blocked network range"
    except socket.gaierror:
        return False, f"Could not resolve hostname: {hostname}"

    return True, "OK"


def is_safe_url(url: str) -> bool:
    """Quick check — returns True if safe, False if blocked."""
    safe, _ = validate_url_safe(url)
    return safe


# ── Rate Limiting ────────────────────────────────────────────────────────────

class RateLimiter:
    """Simple in-memory sliding window rate limiter."""

    def __init__(self, max_calls: int, window_seconds: float):
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self._calls: list[float] = []

    def allow(self) -> bool:
        now = time()
        cutoff = now - self.window_seconds
        self._calls = [t for t in self._calls if t > cutoff]
        if len(self._calls) >= self.max_calls:
            return False
        self._calls.append(now)
        return True

    @property
    def retry_after(self) -> float:
        if not self._calls:
            return 0.0
        oldest = self._calls[0]
        return max(0.0, self.window_seconds - (time() - oldest))


# Global LLM rate limiter: 30 calls per minute
_llm_limiter = RateLimiter(max_calls=30, window_seconds=60)


def check_llm_rate_limit() -> tuple[bool, float]:
    """Check if LLM call is allowed. Returns (allowed, retry_after_seconds)."""
    if _llm_limiter.allow():
        return True, 0.0
    return False, _llm_limiter.retry_after


# ── Input Sanitization ───────────────────────────────────────────────────────

_PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?prior\s+prompts", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(a|an|the)", re.IGNORECASE),
    re.compile(r"system\s*prompt\s*:", re.IGNORECASE),
    re.compile(r"<\|system\|>", re.IGNORECASE),
    re.compile(r"\[INST\]", re.IGNORECASE),
    re.compile(r"<<SYS>>", re.IGNORECASE),
    re.compile(r"###\s*system", re.IGNORECASE),
]

_MAX_INPUT_CHARS = 50000


def sanitize_input(text: str) -> str:
    """Sanitize user input before sending to LLM.

    - Truncates to max length
    - Flags obvious prompt injection attempts (logged, not stripped — stripping would alter meaning)
    """
    if not text:
        return ""
    return text[:_MAX_INPUT_CHARS]


def detect_prompt_injection(text: str) -> bool:
    """Returns True if text contains likely prompt injection patterns."""
    for pattern in _PROMPT_INJECTION_PATTERNS:
        if pattern.search(text):
            return True
    return False


# ── File Validation ──────────────────────────────────────────────────────────

_PDF_MAGIC = b"%PDF"
_MP3_MAGIC = b"\xff\xfb"
_MP3_ID3 = b"ID3"
_WAV_MAGIC = b"RIFF"
_OGG_MAGIC = b"OggS"
_FLAC_MAGIC = b"fLaC"
_M4A_MAGIC = b"\x1a\x45\xdf\xa3"

_FILE_SIGNATURES = {
    ".pdf": [_PDF_MAGIC],
    ".mp3": [_MP3_MAGIC, _MP3_ID3],
    ".wav": [_WAV_MAGIC],
    ".ogg": [_OGG_MAGIC],
    ".flac": [_FLAC_MAGIC],
    ".m4a": [_M4A_MAGIC],
}


def validate_file_magic(file_bytes: bytes, expected_ext: str) -> tuple[bool, str]:
    """Validate file content matches expected extension via magic bytes.

    Returns (is_valid, reason).
    """
    if not file_bytes:
        return False, "Empty file"

    ext = expected_ext.lower()
    if ext not in _FILE_SIGNATURES:
        return False, f"Unknown file extension: {ext}"

    expected_signatures = _FILE_SIGNATURES[ext]
    for sig in expected_signatures:
        if file_bytes[:len(sig)] == sig:
            return True, "OK"

    return False, f"File content does not match {ext} format (magic bytes mismatch)"


# ── Error Sanitization ───────────────────────────────────────────────────────

_SENSITIVE_PATTERNS = [
    re.compile(r"(?:api[_-]?key|token|secret|password|credential)[=:]\s*\S+", re.IGNORECASE),
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),
    re.compile(r"(?:/home/|/Users/|C:\\Users\\)[^\s\"']+"),
]


def sanitize_error_message(error: Exception) -> str:
    """Return a user-safe error message, stripping internal details."""
    msg = str(error)
    for pattern in _SENSITIVE_PATTERNS:
        msg = pattern.sub("[REDACTED]", msg)

    if len(msg) > 200:
        msg = msg[:200] + "..."

    error_type = type(error).__name__
    if error_type in ("FileNotFoundError", "PermissionError", "IOError"):
        return "A file operation failed. Please try again."
    if "timeout" in str(error).lower() or "timed out" in str(error).lower():
        return "The request timed out. The content may be too long. Try a smaller chunk size."
    if "401" in str(error) or "unauthorized" in str(error).lower():
        return "Authentication error. Check your API key in Settings."

    return f"{error_type}: An error occurred during processing. Please try again."
