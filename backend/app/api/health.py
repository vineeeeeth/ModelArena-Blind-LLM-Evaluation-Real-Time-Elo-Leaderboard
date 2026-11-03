"""Health check API router."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.core.redis import redis
from app.schemas import HealthResponse

router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    # 1. DB check
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"error: {str(exc)}"

    # 2. Redis check
    redis_status = "ok"
    try:
        ping = await redis.ping()
        if not ping:
            redis_status = "error: ping returned false"
    except Exception as exc:
        redis_status = f"error: {str(exc)}"

    # 3. Ollama check
    ollama_status = "ok"
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            if resp.status_code != 200:
                ollama_status = f"error: status {resp.status_code}"
    except Exception as exc:
        ollama_status = f"error: {str(exc)}"

    overall = "ok" if (db_status == "ok" and redis_status == "ok") else "degraded"

    return HealthResponse(
        status=overall,
        db=db_status,
        redis=redis_status,
        ollama=ollama_status,
    )

