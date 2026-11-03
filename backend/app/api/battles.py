"""Battles API router – creation, SSE streaming, voting, and result reveal."""

from __future__ import annotations

import json
import time
import uuid
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.api.auth import get_optional_user
from app.core.config import get_settings
from app.core.db import async_session_factory, get_db
from app.core.logging import logger
from app.core.redis import redis
from app.models.tables import (
    AnonSession,
    Battle,
    BattleCategory,
    BattleStatus,
    Model,
    Response,
    SlotEnum,
    User,
    Vote,
    VoteChoice,
)
from app.schemas import (
    BattleCreatedResponse,
    BattleCreateRequest,
    BattleStatusResponse,
    ResponseReveal,
    VoteRequest,
    VoteResultResponse,
)
from app.services.battle_service import create_battle, run_generation
from app.services.rating_service import update_online_elo_vote

router = APIRouter(tags=["battles"])
settings = get_settings()

MIN_VOTE_TIME_MS = 1500


async def check_battle_rate_limit(request: Request, user: Optional[User]) -> None:
    ip = request.client.host if request.client else "unknown"
    session_id = request.state.session_id

    # 1. IP rate limit
    ip_key = f"rate:battle:ip:{ip}"
    ip_count = await redis.incr(ip_key)
    if ip_count == 1:
        await redis.expire(ip_key, 3600)
    if ip_count > settings.ip_battles_per_hour:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: max {settings.ip_battles_per_hour} battles per hour per IP.",
        )

    # 2. User or anon session limit
    if user:
        user_key = f"rate:battle:user:{user.id}"
        u_count = await redis.incr(user_key)
        if u_count == 1:
            await redis.expire(user_key, 3600)
        if u_count > settings.user_battles_per_hour:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: max {settings.user_battles_per_hour} battles per hour for signed-in users.",
            )
    else:
        anon_key = f"rate:battle:anon:{session_id}"
        a_count = await redis.incr(anon_key)
        if a_count == 1:
            await redis.expire(anon_key, 3600)
        if a_count > settings.anon_battles_per_hour:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: max {settings.anon_battles_per_hour} battles per hour for guests. Please log in for higher limits.",
            )


@router.post("", response_model=BattleCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_new_battle(
    data: BattleCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
) -> BattleCreatedResponse:
    await check_battle_rate_limit(request, user)

    session_id_str = getattr(request.state, "session_id", None) or request.cookies.get("arena_session")
    if not session_id_str:
        session_id_str = str(uuid.uuid4())
    session_uuid = uuid.UUID(session_id_str)

    user_id = user.id if user else None

    battle = await create_battle(
        db=db,
        prompt=data.prompt,
        session_id=session_uuid,
        user_id=user_id,
        category_override=data.category,
    )
    await db.commit()

    return BattleCreatedResponse(
        battle_id=battle.id,
        category=battle.category.value,
    )


@router.get("/{battle_id}", response_model=BattleStatusResponse)
async def get_battle_status(
    battle_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> BattleStatusResponse:
    battle = await db.get(Battle, battle_id)
    if not battle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Battle not found.")

    return BattleStatusResponse(
        battle_id=battle.id,
        status=battle.status.value,
        category=battle.category.value,
        prompt=battle.prompt_text,
    )


@router.get("/{battle_id}/stream/{slot}")
async def stream_battle_slot(
    battle_id: uuid.UUID,
    slot: str,
):
    if slot not in ("A", "B"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slot must be 'A' or 'B'.")

    slot_enum = SlotEnum(slot)

    async def event_generator() -> AsyncGenerator[dict[str, str], None]:
        async with async_session_factory() as session:
            try:
                async for token in run_generation(session, battle_id, slot_enum):
                    yield {
                        "event": "token",
                        "data": json.dumps({"token": token}),
                    }
                await session.commit()
                yield {"event": "done", "data": json.dumps({"status": "completed"})}
            except Exception as exc:
                await session.rollback()
                logger.error("stream_error", battle_id=str(battle_id), slot=slot, error=str(exc))
                yield {"event": "error", "data": json.dumps({"error": "Generation failed. Try again."})}

    return EventSourceResponse(event_generator())


@router.post("/{battle_id}/vote", response_model=VoteResultResponse)
async def submit_vote(
    battle_id: uuid.UUID,
    data: VoteRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
) -> VoteResultResponse:
    battle = await db.get(Battle, battle_id)
    if not battle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Battle not found.")

    if battle.status != BattleStatus.ready:
        if battle.status == BattleStatus.voted:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This battle has already been voted on.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot vote yet. Battle status is '{battle.status.value}'. Both models must finish generating first.",
        )

    # Check for suspiciously fast votes (< 1.5 seconds)
    if data.time_to_vote_ms is not None and data.time_to_vote_ms < MIN_VOTE_TIME_MS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Suspiciously fast vote ({data.time_to_vote_ms}ms). Minimum evaluation time is {MIN_VOTE_TIME_MS}ms.",
        )

    session_id_str = getattr(request.state, "session_id", None) or request.cookies.get("arena_session")
    session_uuid = uuid.UUID(session_id_str) if session_id_str else battle.session_id

    # Ensure anon session exists in DB to prevent foreign key violation
    anon = await db.get(AnonSession, session_uuid)
    if not anon:
        anon = AnonSession(id=session_uuid, user_id=user.id if user else None)
        db.add(anon)
        await db.flush()

    choice_enum = VoteChoice(data.choice)
    vote = Vote(
        battle_id=battle.id,
        choice=choice_enum,
        voter_session_id=session_uuid,
        voter_user_id=user.id if user else None,
        time_to_vote_ms=data.time_to_vote_ms,
        is_simulated=False,
    )
    db.add(vote)
    battle.status = BattleStatus.voted

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        logger.warning("vote_integrity_error", error=str(exc))
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A vote has already been recorded for this battle.")

    # Update online Elo immediately
    await update_online_elo_vote(db, battle, vote)

    # Fetch responses and model names for the reveal payload
    resp_query = await db.execute(
        select(Response, Model)
        .join(Model, Response.model_id == Model.id)
        .where(Response.battle_id == battle.id)
        .order_by(Response.slot)
    )
    reveals = []
    for resp_row, model_row in resp_query.all():
        reveals.append(
            ResponseReveal(
                slot=resp_row.slot.value,
                model_name=model_row.display_name,
                model_slug=model_row.slug,
                input_tokens=resp_row.input_tokens,
                output_tokens=resp_row.output_tokens,
                ttft_ms=resp_row.ttft_ms,
                total_latency_ms=resp_row.total_latency_ms,
                cost_usd=float(resp_row.cost_usd),
            )
        )

    return VoteResultResponse(
        choice=choice_enum.value,
        responses=reveals,
    )

