"""Google Gemini LLM provider – streams generateContent via the Gemini REST API."""

from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator

import httpx

from app.core.config import get_settings
from app.services.providers.base import LLMProvider


class GeminiProvider(LLMProvider):
    provider_name: str = "gemini"

    def __init__(self) -> None:
        self._settings = get_settings()
        self._api_key = self._settings.google_api_key
        self._base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def stream_completion(
        self,
        model_id: str,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
    ) -> AsyncGenerator[str, None]:
        url = (
            f"{self._base_url}/models/{model_id}:streamGenerateContent"
            f"?alt=sse&key={self._api_key}"
        )
        payload: dict = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature if temperature is not None else 0.3,
            },
        }
        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            try:
                async with client.stream("POST", url, json=payload) as resp:
                    if resp.status_code == 200:
                        async for raw_line in resp.aiter_lines():
                            line = raw_line.strip()
                            if not line or not line.startswith("data: "):
                                continue
                            data_str = line[len("data: "):]
                            try:
                                chunk = json.loads(data_str)
                            except json.JSONDecodeError:
                                continue
                            candidates = chunk.get("candidates", [])
                            if candidates:
                                content = candidates[0].get("content", {})
                                parts = content.get("parts", [])
                                for part in parts:
                                    token = part.get("text", "")
                                    if token:
                                        yield token
                        return
            except Exception:
                pass

            # Fallback to direct generateContent if streaming endpoint is unavailable/503
            non_stream_url = (
                f"{self._base_url}/models/{model_id}:generateContent?key={self._api_key}"
            )
            resp = await client.post(non_stream_url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                for part in parts:
                    text = part.get("text", "")
                    words = text.split(" ")
                    for i, w in enumerate(words):
                        yield w + (" " if i < len(words) - 1 else "")
                        await asyncio.sleep(0.015)

    async def count_tokens(self, text: str) -> int:
        words = len(text.split())
        return int(words * 1.3)

