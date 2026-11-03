"""Abstract base class for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncGenerator


class LLMProvider(ABC):
    """Interface every LLM provider must implement."""

    provider_name: str = ""

    @abstractmethod
    async def stream_completion(
        self,
        model_id: str,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
    ) -> AsyncGenerator[str, None]:
        """Yield token strings as they arrive from the model."""
        ...  # pragma: no cover

    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """Return an approximate token count for *text*."""
        ...  # pragma: no cover
