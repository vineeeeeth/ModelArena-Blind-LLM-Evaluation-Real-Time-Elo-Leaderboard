"""Leaderboard API router."""

from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.redis import redis
from app.models.tables import BattleCategory
from app.schemas import LeaderboardEntry, LeaderboardResponse
from app.services.rating_service import compute_full_rankings

router = APIRouter(tags=["leaderboard"])


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    category: Optional[str] = Query(None, description="Category filter (general, coding, math, hindi, summarization)"),
    include_simulated: bool = Query(True, description="Whether to include simulated demo data"),
    db: AsyncSession = Depends(get_db),
) -> LeaderboardResponse:
    cat_enum = None
    if category and category.lower() != "overall":
        try:
            cat_enum = BattleCategory(category.lower())
        except ValueError:
            pass

    cache_key = f"leaderboard:{category.lower() if category else 'overall'}:sim_{include_simulated}"
    cached = await redis.get(cache_key)

    if cached:
        data = json.loads(cached)
        entries = [LeaderboardEntry(**item) for item in data]
        return LeaderboardResponse(
            category=category,
            entries=entries,
            includes_simulated=include_simulated,
        )

    # Compute live if not in cache
    snapshots = await compute_full_rankings(db, category=cat_enum, include_simulated=include_simulated)
    # Refresh cache query
    cached = await redis.get(cache_key)
    if cached:
        data = json.loads(cached)
        entries = [LeaderboardEntry(**item) for item in data]
    else:
        entries = []

    return LeaderboardResponse(
        category=category,
        entries=entries,
        includes_simulated=include_simulated,
    )

