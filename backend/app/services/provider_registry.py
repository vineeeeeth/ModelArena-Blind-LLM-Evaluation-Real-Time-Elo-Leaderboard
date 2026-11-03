"""Provider registry – discovers available LLM providers from env vars."""

from __future__ import annotations

from typing import Dict

from app.core.config import get_settings
from app.core.logging import logger
from app.services.providers.base import LLMProvider
from app.services.providers.ollama import OllamaProvider


_registry: Dict[str, LLMProvider] = {}
_initialised: bool = False


def _init_registry() -> None:
    global _initialised
    if _initialised:
        return

    settings = get_settings()

    # Ollama is always available (local)
    _registry["ollama"] = OllamaProvider()

    if settings.openai_api_key:
        from app.services.providers.openai import OpenAIProvider
        _registry["openai"] = OpenAIProvider()

    if settings.anthropic_api_key:
        from app.services.providers.anthropic import AnthropicProvider
        _registry["anthropic"] = AnthropicProvider()

    if settings.google_api_key:
        from app.services.providers.gemini import GeminiProvider
        _registry["gemini"] = GeminiProvider()

    _initialised = True


def get_provider(provider_name: str) -> LLMProvider:
    """Return the provider instance for *provider_name*, or raise KeyError."""
    _init_registry()
    provider = _registry.get(provider_name)
    if provider is None:
        raise KeyError(
            f"Provider '{provider_name}' is not available. "
            f"Available: {list(_registry.keys())}"
        )
    return provider


def list_providers() -> list[str]:
    """Return names of all available providers."""
    _init_registry()
    return list(_registry.keys())
