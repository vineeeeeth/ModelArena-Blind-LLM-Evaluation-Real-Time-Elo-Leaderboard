"""Admin API router."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.core.db import get_db
from app.models.tables import BattleCategory, Model, User, UserRole
from app.schemas import ModelAdminUpdate, ModelResponse
from app.services.rating_service import compute_full_rankings

router = APIRouter(tags=["admin"])


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required.",
        )
    return current_user


@router.get("/models", response_model=list[ModelResponse])
async def list_all_models(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> list[ModelResponse]:
    res = await db.execute(select(Model).order_by(Model.id))
    models = res.scalars().all()
    return [ModelResponse.model_validate(m) for m in models]


@router.patch("/models/{model_id}", response_model=ModelResponse)
async def update_model(
    model_id: int,
    data: ModelAdminUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> ModelResponse:
    model = await db.get(Model, model_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found.")

    if data.is_enabled is not None:
        model.is_enabled = data.is_enabled
    if data.input_price_per_mtok is not None:
        model.input_price_per_mtok = data.input_price_per_mtok
    if data.output_price_per_mtok is not None:
        model.output_price_per_mtok = data.output_price_per_mtok

    await db.commit()
    return ModelResponse.model_validate(model)


@router.post("/recompute")
async def trigger_recompute(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict[str, str]:
    # Recompute overall
    await compute_full_rankings(db, category=None, include_simulated=True)
    # Recompute each category
    for cat in BattleCategory:
        await compute_full_rankings(db, category=cat, include_simulated=True)

    return {"message": "Rankings recomputed successfully for overall and all categories."}

