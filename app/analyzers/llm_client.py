from typing import Generator

from tenacity import retry, stop_after_attempt, wait_exponential
from openai import OpenAI

from app.config import BASE_URL, MODEL_NAME, get_api_key


class LLMClient:
    def __init__(self, api_key: str | None = None):
        key = api_key or get_api_key()
        self.base_url = BASE_URL
        self.model = MODEL_NAME
        self._client = OpenAI(api_key=key, base_url=self.base_url)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def _call_api(self, system_prompt, user_message, temperature, max_tokens, retries_left=3):
        from openai import APIError
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except APIError:
            raise

    def send(
        self,
        system_prompt,
        user_message,
        temperature=0.3,
        max_tokens=4000,
        max_retries=None,
    ):
        from openai import APIError, APITimeoutError
        retries = max_retries if max_retries is not None else 3
        if retries == 3:
            return self._call_api(
                system_prompt=system_prompt,
                user_message=user_message,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        last_error = None
        for attempt in range(retries):
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content or ""
            except (APIError, APITimeoutError, ConnectionError) as e:
                last_error = e
        raise last_error

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
        system_prompt,
        user_message,
        temperature=0.3,
        max_tokens=4000,
    ):
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
