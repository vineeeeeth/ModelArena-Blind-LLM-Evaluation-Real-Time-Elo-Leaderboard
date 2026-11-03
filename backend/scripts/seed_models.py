"""Seed models registry with pricing and provider configs."""

from __future__ import annotations

import asyncio
from decimal import Decimal

from sqlalchemy import select

from app.core.config import get_settings
from app.core.db import async_session_factory
from app.core.logging import logger
from app.models.tables import Model

settings = get_settings()

INITIAL_MODELS = [
    # Ollama local open models ($0 pricing)
    {
        "slug": "llama-3.2-3b",
        "display_name": "Llama 3.2 3B",
        "provider": "ollama",
        "provider_model_id": "llama3.2:3b",
        "input_price_per_mtok": Decimal("0.0"),
        "output_price_per_mtok": Decimal("0.0"),
        "is_open_source": True,
        "is_enabled": True,
    },
    {
        "slug": "qwen-2.5-3b",
        "display_name": "Qwen 2.5 3B",
        "provider": "ollama",
        "provider_model_id": "qwen2.5:3b",
        "input_price_per_mtok": Decimal("0.0"),
        "output_price_per_mtok": Decimal("0.0"),
        "is_open_source": True,
        "is_enabled": True,
    },
    {
        "slug": "gemma-2-2b",
        "display_name": "Gemma 2 2B",
        "provider": "ollama",
        "provider_model_id": "gemma2:2b",
        "input_price_per_mtok": Decimal("0.0"),
        "output_price_per_mtok": Decimal("0.0"),
        "is_open_source": True,
        "is_enabled": True,
    },
    {
        "slug": "phi-3-mini",
        "display_name": "Phi-3 Mini",
        "provider": "ollama",
        "provider_model_id": "phi3:mini",
        "input_price_per_mtok": Decimal("0.0"),
        "output_price_per_mtok": Decimal("0.0"),
        "is_open_source": True,
        "is_enabled": True,
    },
    # Optional Hosted Models
    {
        "slug": "gpt-4o-mini",
        "display_name": "GPT-4o Mini",
        "provider": "openai",
        "provider_model_id": "gpt-4o-mini",
        "input_price_per_mtok": Decimal("0.1500"),
        "output_price_per_mtok": Decimal("0.6000"),
        "is_open_source": False,
        "is_enabled": bool(settings.openai_api_key),
    },
    {
        "slug": "gpt-4o",
        "display_name": "GPT-4o",
        "provider": "openai",
        "provider_model_id": "gpt-4o",
        "input_price_per_mtok": Decimal("2.5000"),
        "output_price_per_mtok": Decimal("10.0000"),
        "is_open_source": False,
        "is_enabled": bool(settings.openai_api_key),
    },
    {
        "slug": "claude-3-haiku",
        "display_name": "Claude 3 Haiku",
        "provider": "anthropic",
        "provider_model_id": "claude-3-haiku-20240307",
        "input_price_per_mtok": Decimal("0.2500"),
        "output_price_per_mtok": Decimal("1.2500"),
        "is_open_source": False,
        "is_enabled": bool(settings.anthropic_api_key),
    },
    {
        "slug": "gemini-flash",
        "display_name": "Google Gemini Flash",
        "provider": "gemini",
        "provider_model_id": "gemini-3.5-flash",
        "input_price_per_mtok": Decimal("0.0750"),
        "output_price_per_mtok": Decimal("0.3000"),
        "is_open_source": False,
        "is_enabled": bool(settings.google_api_key),
    },
]


async def seed_models():
    async with async_session_factory() as session:
        for m_data in INITIAL_MODELS:
            existing = (
                await session.execute(select(Model).where(Model.slug == m_data["slug"]))
            ).scalar_one_or_none()
            if not existing:
                model = Model(**m_data)
                session.add(model)
                logger.info("model_seeded", slug=m_data["slug"])
            else:
                existing.display_name = m_data["display_name"]
                existing.provider = m_data["provider"]
                existing.provider_model_id = m_data["provider_model_id"]
                existing.input_price_per_mtok = m_data["input_price_per_mtok"]
                existing.output_price_per_mtok = m_data["output_price_per_mtok"]
                existing.is_open_source = m_data["is_open_source"]
                if not m_data["is_open_source"]:
                    existing.is_enabled = m_data["is_enabled"]
        await session.commit()
    logger.info("seeding_completed")


if __name__ == "__main__":
    asyncio.run(seed_models())

