"""Statistics API router – pairwise win matrix, rating trends, cost-latency trade-offs."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.tables import Battle, BattleCategory, Model, PairwiseStats, RatingSnapshot, Response
from app.schemas import CostLatencyPoint, ModelStatsResponse, TrendPoint, TrendResponse, WinMatrixResponse

router = APIRouter(tags=["stats"])


@router.get("/win-matrix", response_model=WinMatrixResponse)
async def get_win_matrix(
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> WinMatrixResponse:
    # 1. Get enabled models
    models_res = await db.execute(select(Model).where(Model.is_enabled.is_(True)).order_by(Model.id))
    models = list(models_res.scalars().all())
    model_slugs = [m.slug for m in models]
    id_to_idx = {m.id: idx for idx, m in enumerate(models)}

    n = len(models)
    matrix: list[list[Optional[float]]] = [[None for _ in range(n)] for _ in range(n)]

    cat_str = category.lower() if category and category.lower() != "overall" else None

    # Query pairwise stats
    query = select(PairwiseStats).where(PairwiseStats.category == cat_str)
    stats_res = await db.execute(query)
    for p in stats_res.scalars().all():
        if p.model_a_id in id_to_idx and p.model_b_id in id_to_idx:
            i = id_to_idx[p.model_a_id]
            j = id_to_idx[p.model_b_id]
            total = p.a_wins + p.b_wins + p.ties
            if total > 0:
                win_fraction = round((p.a_wins + 0.5 * p.ties) / total, 3)
                matrix[i][j] = win_fraction
                matrix[j][i] = round(1.0 - win_fraction, 3)

    return WinMatrixResponse(
        category=category,
        model_slugs=model_slugs,
        matrix=matrix,
    )


@router.get("/battle-counts")
async def get_battle_counts(db: AsyncSession = Depends(get_db)) -> dict[str, int]:
    res = await db.execute(
        select(Battle.category, func.count(Battle.id)).group_by(Battle.category)
    )
    counts = {r[0].value: r[1] for r in res.all()}
    total = sum(counts.values())
    counts["total"] = total
    return counts


@router.get("/cost-latency", response_model=list[CostLatencyPoint])
async def get_cost_latency(db: AsyncSession = Depends(get_db)) -> list[CostLatencyPoint]:
    query = (
        select(
            Model.slug,
            Model.display_name,
            func.avg(Response.cost_usd),
            func.avg(Response.total_latency_ms),
        )
        .join(Response, Model.id == Response.model_id)
        .where(Model.is_enabled.is_(True))
        .group_by(Model.id, Model.slug, Model.display_name)
    )
    res = await db.execute(query)
    points = []
    for slug, name, avg_cost, avg_lat in res.all():
        # Get latest overall snapshot for Elo
        elo_q = await db.execute(
            select(RatingSnapshot.elo)
            .join(Model, RatingSnapshot.model_id == Model.id)
            .where(Model.slug == slug, RatingSnapshot.category.is_(None))
            .order_by(RatingSnapshot.computed_at.desc())
            .limit(1)
        )
        elo = float(elo_q.scalar_one_or_none() or 1000.0)
        points.append(
            CostLatencyPoint(
                model_slug=slug,
                model_name=name,
                avg_cost_usd=round(float(avg_cost or 0), 6),
                avg_latency_ms=round(float(avg_lat or 0), 2),
                elo=elo,
            )
        )
    return points


@router.get("/trends", response_model=list[TrendResponse])
async def get_rating_trends(
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[TrendResponse]:
    cat_str = category.lower() if category and category.lower() != "overall" else None

    models_res = await db.execute(select(Model).where(Model.is_enabled.is_(True)))
    models = list(models_res.scalars().all())

    trends: list[TrendResponse] = []
    for m in models:
        q = (
            select(RatingSnapshot)
            .where(RatingSnapshot.model_id == m.id, RatingSnapshot.category == cat_str)
            .order_by(RatingSnapshot.computed_at.asc())
            .limit(50)
        )
        res = await db.execute(q)
        points = [
            TrendPoint(
                computed_at=s.computed_at,
                elo=float(s.elo),
                bt_score=float(s.bt_score),
            )
            for s in res.scalars().all()
        ]
        trends.append(
            TrendResponse(
                model_slug=m.slug,
                category=category,
                points=points,
            )
        )
    return trends

