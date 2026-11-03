"""Ollama LLM provider – streams completions via the local Ollama HTTP API."""

from __future__ import annotations

import json
from typing import AsyncGenerator

import httpx

from app.core.config import get_settings
from app.core.logging import logger
from app.services.providers.base import LLMProvider


class OllamaProvider(LLMProvider):
    provider_name: str = "ollama"

    def __init__(self) -> None:
        self._settings = get_settings()
        self._base_url = self._settings.ollama_base_url.rstrip("/")

    async def stream_completion(
        self,
        model_id: str,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
    ) -> AsyncGenerator[str, None]:
        url = f"{self._base_url}/api/generate"
        payload: dict = {
            "model": model_id,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature if temperature is not None else 0.3,
                "top_p": 0.9,
                "top_k": 40,
                "repeat_penalty": 1.15,
                "num_ctx": 4096,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            async with client.stream("POST", url, json=payload) as resp:
                resp.raise_for_status()
                async for raw_line in resp.aiter_lines():
                    if not raw_line.strip():
                        continue
                    try:
                        chunk = json.loads(raw_line)
                    except json.JSONDecodeError:
                        continue
                    token = chunk.get("response", "")
                    if token:
                        yield token
                    if chunk.get("done", False):
                        return

    async def count_tokens(self, text: str) -> int:
        words = len(text.split())
        return int(words * 1.3)

    async def pull_model(self, model_id: str) -> None:
        """Pull a model so it's available locally."""
        url = f"{self._base_url}/api/pull"
        payload = {"name": model_id, "stream": False}
        async with httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=10.0)) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                logger.info("ollama_model_pulled", model=model_id)
            else:
                logger.warning(
                    "ollama_model_pull_failed",
                    model=model_id,
                    status=resp.status_code,
                    body=resp.text[:500],
                )
