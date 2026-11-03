"""Anthropic LLM provider – streams messages via the Anthropic REST API."""

from __future__ import annotations

import json
from typing import AsyncGenerator

import httpx

from app.core.config import get_settings
from app.services.providers.base import LLMProvider


class AnthropicProvider(LLMProvider):
    provider_name: str = "anthropic"

    def __init__(self) -> None:
        self._settings = get_settings()
        self._api_key = self._settings.anthropic_api_key
        self._base_url = "https://api.anthropic.com/v1"

    async def stream_completion(
        self,
        model_id: str,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
    ) -> AsyncGenerator[str, None]:
        url = f"{self._base_url}/messages"
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model_id,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
            "temperature": temperature if temperature is not None else 0.3,
        }
        if system_prompt:
            payload["system"] = system_prompt

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                async for raw_line in resp.aiter_lines():
                    line = raw_line.strip()
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[len("data: "):]
                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue
                    event_type = chunk.get("type", "")
                    if event_type == "content_block_delta":
                        delta = chunk.get("delta", {})
                        token = delta.get("text", "")
                        if token:
                            yield token
                    elif event_type == "message_stop":
                        return

    async def count_tokens(self, text: str) -> int:
        words = len(text.split())
        return int(words * 1.3)
