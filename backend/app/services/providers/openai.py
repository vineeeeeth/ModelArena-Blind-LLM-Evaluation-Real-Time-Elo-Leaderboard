"""OpenAI LLM provider – streams chat completions via the OpenAI REST API."""

from __future__ import annotations

import json
from typing import AsyncGenerator

import httpx

from app.core.config import get_settings
from app.services.providers.base import LLMProvider


class OpenAIProvider(LLMProvider):
    provider_name: str = "openai"

    def __init__(self) -> None:
        self._settings = get_settings()
        self._api_key = self._settings.openai_api_key
        if self._api_key.startswith("gsk_"):
            self._base_url = "https://api.groq.com/openai/v1"
        else:
            self._base_url = "https://api.openai.com/v1"

    async def stream_completion(
        self,
        model_id: str,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
    ) -> AsyncGenerator[str, None]:
        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Map model name if using Groq API key
        target_model = model_id
        if self._api_key.startswith("gsk_"):
            if "mini" in model_id:
                target_model = "openai/gpt-oss-20b"
            elif "qwen" in model_id:
                target_model = "qwen/qwen3.8-27b"
            else:
                target_model = "openai/gpt-oss-120b"

        payload = {
            "model": target_model,
            "messages": messages,
            "stream": True,
            "temperature": temperature if temperature is not None else 0.3,
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                async for raw_line in resp.aiter_lines():
                    line = raw_line.strip()
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[len("data: "):]
                    if data_str == "[DONE]":
                        return
                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue
                    choices = chunk.get("choices", [])
                    if choices:
                        delta = choices[0].get("delta", {})
                        token = delta.get("content", "")
                        if token:
                            yield token

    async def count_tokens(self, text: str) -> int:
        words = len(text.split())
        return int(words * 1.3)
