import hashlib
import time
from collections import OrderedDict
from typing import Generator

from tenacity import retry, stop_after_attempt, wait_exponential
from openai import OpenAI

from app.config import BASE_URL, MODEL_NAME, get_api_key


class ResponseCache:
    """LRU cache for LLM responses. Key = hash of model + prompt pair."""

    def __init__(self, max_size: int = 50, ttl: int = 3600):
        self._cache: OrderedDict[str, tuple[str, float]] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl

    def get(self, model: str, system_prompt: str, user_message: str) -> str | None:
        key = self._make_key(model, system_prompt, user_message)
        if key in self._cache:
            result, ts = self._cache[key]
            if time.time() - ts < self._ttl:
                self._cache.move_to_end(key)
                return result
            del self._cache[key]
        return None

    def put(self, model: str, system_prompt: str, user_message: str, response: str) -> None:
        key = self._make_key(model, system_prompt, user_message)
        if key in self._cache:
            del self._cache[key]
        self._cache[key] = (response, time.time())
        if len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    @staticmethod
    def _make_key(model: str, system_prompt: str, user_message: str) -> str:
        raw = f"{model}:{system_prompt}:{user_message}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]


_response_cache = ResponseCache()


class LLMClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None, model: str | None = None):
        key = api_key or get_api_key()
        self.base_url = base_url or BASE_URL
        self.model = model or MODEL_NAME
        self._client = OpenAI(api_key=key, base_url=self.base_url)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def send(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> str:
        cached = _response_cache.get(self.model, system_prompt, user_message)
        if cached is not None:
            return cached

        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        result = response.choices[0].message.content or ""
        _response_cache.put(self.model, system_prompt, user_message, result)
        return result

    def translate_text(self, text: str, source_language: str, target_language: str = "English") -> str:
        if not text.strip():
            return text
        max_chars = 15000
        chunks = [text[i:i+max_chars] for i in range(0, len(text), max_chars)]
        translations = []
        for chunk in chunks:
            prompt = (
                f"Translate the following {source_language} text to {target_language}. "
                f"Preserve all meaning, tone, and formatting. Output only the translation.\n\n{chunk}"
            )
            try:
                result = self.send(
                    system_prompt="You are a precise translator. Translate accurately and preserve all meaning, nuance, and structure.",
                    user_message=prompt,
                    temperature=0.1,
                    max_tokens=8000,
                )
                translations.append(result)
            except Exception:
                translations.append(chunk)
        return " ".join(translations)

    def send_stream(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> Generator[str, None, None]:
        stream = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content
