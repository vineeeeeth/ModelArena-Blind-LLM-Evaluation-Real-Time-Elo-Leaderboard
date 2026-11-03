"""Background worker tasks using Arq."""

from __future__ import annotations

from app.core.db import async_session_factory
from app.core.logging import logger
from app.models.tables import BattleCategory
from app.services.rating_service import compute_full_rankings


async def recompute_ratings_task(ctx: dict) -> str:
    """Periodic task to recompute Elo, Bradley-Terry, and Bootstrap CIs."""
    logger.info("recompute_ratings_started")
    async with async_session_factory() as session:
        try:
            # Overall
            await compute_full_rankings(session, category=None, include_simulated=True)
            await compute_full_rankings(session, category=None, include_simulated=False)

            # Each category
            for cat in BattleCategory:
                await compute_full_rankings(session, category=cat, include_simulated=True)
                await compute_full_rankings(session, category=cat, include_simulated=False)

            logger.info("recompute_ratings_completed")
            return "ok"
        except Exception as exc:
            logger.error("recompute_ratings_failed", error=str(exc))
            raise

