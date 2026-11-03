"""Battle service – model selection, battle creation, LLM generation, status management."""

from __future__ import annotations

import random
import time
import uuid
from typing import AsyncGenerator, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.core.redis import redis
from app.models.tables import (
    AnonSession,
    Battle,
    BattleCategory,
    BattleStatus,
    CategorySource,
    Model,
    Response,
    SlotEnum,
)
from app.services.classifier import classify_prompt
from app.services.pricing import compute_cost
from app.services.provider_registry import get_provider


async def select_model_pair(db: AsyncSession) -> tuple[Model, Model]:
    """Select 2 different enabled models, weighted toward under-sampled pairs."""
    result = await db.execute(select(Model).where(Model.is_enabled.is_(True)))
    models = list(result.scalars().all())

    # Check which ollama models are currently downloaded
    available_ollama_ids: set[str] = set()
    try:
        from app.core.config import get_settings
        import httpx
        cfg = get_settings()
        async with httpx.AsyncClient(timeout=1.5) as client:
            resp = await client.get(f"{cfg.ollama_base_url}/api/tags")
            if resp.status_code == 200:
                for item in resp.json().get("models", []):
                    name = item.get("name", "")
                    available_ollama_ids.add(name)
                    if ":" in name:
                        available_ollama_ids.add(name.split(":")[0])
    except Exception:
        pass

    if available_ollama_ids:
        filtered = [
            m for m in models
            if m.provider != "ollama" or m.provider_model_id in available_ollama_ids or any(m.provider_model_id.startswith(tag) for tag in available_ollama_ids)
        ]
        if len(filtered) >= 2:
            models = filtered

    if len(models) < 2:
        raise ValueError("Need at least 2 enabled models to create a battle.")

    # Count battles per model to weight toward under-sampled ones
    battle_counts: dict[int, int] = {}
    for m in models:
        count_q = await db.execute(
            select(func.count()).where(
                (Battle.model_a_id == m.id) | (Battle.model_b_id == m.id)
            )
        )
        battle_counts[m.id] = count_q.scalar_one()

    # Inverse-frequency weights: models with fewer battles get higher weight
    max_count = max(battle_counts.values()) if battle_counts else 1
    weights = []
    for m in models:
        w = max_count - battle_counts.get(m.id, 0) + 1
        weights.append(w)

    # Weighted sample for first model
    model_a = random.choices(models, weights=weights, k=1)[0]

    # For second model, exclude model_a and re-weight
    remaining = [m for m in models if m.id != model_a.id]
    remaining_weights = [
        max_count - battle_counts.get(m.id, 0) + 1 for m in remaining
    ]
    model_b = random.choices(remaining, weights=remaining_weights, k=1)[0]

    # Randomly assign to slot A or B
    if random.random() < 0.5:
        return model_a, model_b
    return model_b, model_a


async def create_battle(
    db: AsyncSession,
    prompt: str,
    session_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = None,
    category_override: Optional[str] = None,
) -> Battle:
    """Create a new battle with two model slots."""

    # Ensure anon session exists
    existing = await db.get(AnonSession, session_id)
    if not existing:
        anon = AnonSession(id=session_id)
        if user_id:
            anon.user_id = user_id
        db.add(anon)
        await db.flush()

    # Classify category
    if category_override:
        category = BattleCategory(category_override)
        cat_source = CategorySource.user
    else:
        category = classify_prompt(prompt)
        cat_source = CategorySource.auto

    # Select models
    model_a, model_b = await select_model_pair(db)

    battle = Battle(
        prompt_text=prompt,
        category=category,
        category_source=cat_source,
        model_a_id=model_a.id,
        model_b_id=model_b.id,
        session_id=session_id,
        user_id=user_id,
        status=BattleStatus.generating,
    )
    db.add(battle)
    await db.flush()

    # Create response rows for each slot
    resp_a = Response(
        battle_id=battle.id,
        slot=SlotEnum.A,
        model_id=model_a.id,
    )
    resp_b = Response(
        battle_id=battle.id,
        slot=SlotEnum.B,
        model_id=model_b.id,
    )
    db.add(resp_a)
    db.add(resp_b)
    await db.flush()

    logger.info(
        "battle_created",
        battle_id=str(battle.id),
        category=category.value,
        model_a=model_a.slug,
        model_b=model_b.slug,
    )

    return battle


def get_system_prompt_and_temp(category: BattleCategory) -> tuple[str, float]:
    """Returns specialized, anti-hallucination system prompt and calibrated temperature."""
    base_guidance = (
        "You are an expert, truthful, and highly capable AI assistant matching the quality of top-tier models like GPT-4 and Claude. "
        "Strict Guidelines:\n"
        "1. FACTUAL ACCURACY: Strictly avoid hallucinations or fabricated claims. Present only verifiable facts. If uncertain, state what is known and clarify limits.\n"
        "2. STRUCTURE & CLARITY: Present answers logically using clear markdown formatting, headings, bullet points, and code blocks.\n"
        "3. DEPTH & RIGOR: Answer the prompt thoroughly and directly without filler, superficiality, or evasiveness."
    )

    if category == BattleCategory.coding:
        system = (
            f"{base_guidance}\n\n"
            "Role: Principal Software Architect.\n"
            "- Write clean, robust, bug-free, production-ready code.\n"
            "- Handle edge cases and include clear comments on complex logic.\n"
            "- Use proper markdown code blocks with explicit language tags.\n"
            "- Provide concise usage examples and explain key trade-offs."
        )
        return system, 0.2  # Low temperature for deterministic, bug-free code

    elif category == BattleCategory.math:
        system = (
            f"{base_guidance}\n\n"
            "Role: Expert Mathematician and Analytical Problem Solver.\n"
            "- Think step by step. Show intermediate derivations and calculations clearly.\n"
            "- Verify all arithmetic before stating the conclusion.\n"
            "- State the final answer prominently at the end."
        )
        return system, 0.1  # Very low temperature for maximum math precision

    elif category == BattleCategory.hindi:
        system = (
            f"{base_guidance}\n\n"
            "Role: हिंदी भाषा एवं विषय विशेषज्ञ (Hindi Language & Domain Expert).\n"
            "- अपने सभी उत्तर शुद्ध, स्वाभाविक, धाराप्रवाह और मानक हिंदी (देवनागरी लिपि) में दें।\n"
            "- व्याकरण और वर्तनी का विशेष ध्यान रखें।\n"
            "- तथ्यात्मक और प्रामाणिक उत्तर ही दें, कोई मनगढ़ंत बात न लिखें।"
        )
        return system, 0.3

    elif category == BattleCategory.summarization:
        system = (
            f"{base_guidance}\n\n"
            "Role: Executive Intelligence Analyst.\n"
            "- Extract key takeaways, core findings, and actionable points.\n"
            "- Remain strictly faithful to the source material without outside speculation or hallucinated facts.\n"
            "- Use clean bullet points and bold highlights for critical points."
        )
        return system, 0.2

    else:
        system = (
            f"{base_guidance}\n\n"
            "- Answer directly, objectively, and comprehensively.\n"
            "- If the question involves history, science, or technical concepts, be rigorously accurate and clear."
        )
        return system, 0.3


async def run_generation(
    db: AsyncSession,
    battle_id: uuid.UUID,
    slot: SlotEnum,
) -> AsyncGenerator[str, None]:
    """Run LLM generation for a slot and stream tokens.

    Updates the Response row with content, tokens, latency, and cost on completion.
    """
    # Load the response row + battle
    result = await db.execute(
        select(Response).where(
            Response.battle_id == battle_id,
            Response.slot == slot,
        )
    )
    response_row = result.scalar_one_or_none()
    if response_row is None:
        raise ValueError(f"No response row for battle={battle_id}, slot={slot}")

    battle = await db.get(Battle, battle_id)
    if battle is None:
        raise ValueError(f"Battle {battle_id} not found")

    model = await db.get(Model, response_row.model_id)
    if model is None:
        raise ValueError(f"Model {response_row.model_id} not found")

    provider = get_provider(model.provider)

    system_prompt, temp = get_system_prompt_and_temp(battle.category)

    collected_tokens: list[str] = []
    start_time = time.perf_counter()
    ttft: Optional[float] = None

    try:
        async for token in provider.stream_completion(
            model.provider_model_id,
            battle.prompt_text,
            system_prompt=system_prompt,
            temperature=temp,
        ):
            if ttft is None:
                ttft = (time.perf_counter() - start_time) * 1000
            collected_tokens.append(token)
            yield token
    except Exception as exc:
        elapsed = (time.perf_counter() - start_time) * 1000
        response_row.error = str(exc)[:2000]
        response_row.total_latency_ms = int(elapsed)
        await db.flush()
        logger.exception(
            "generation_error",
            battle_id=str(battle_id),
            slot=slot.value,
            model=model.slug,
        )
        return

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    full_content = "".join(collected_tokens)

    input_tokens = await provider.count_tokens(battle.prompt_text)
    output_tokens = await provider.count_tokens(full_content)
    cost = compute_cost(
        input_tokens,
        output_tokens,
        model.input_price_per_mtok,
        model.output_price_per_mtok,
    )

    response_row.content = full_content
    response_row.input_tokens = input_tokens
    response_row.output_tokens = output_tokens
    response_row.ttft_ms = int(ttft) if ttft is not None else None
    response_row.total_latency_ms = int(elapsed_ms)
    response_row.cost_usd = cost
    await db.flush()

    # Check if we should mark battle ready
    await _maybe_mark_ready(db, battle_id)


async def _maybe_mark_ready(db: AsyncSession, battle_id: uuid.UUID) -> None:
    """If both responses are complete (have content and no error), mark battle as ready."""
    result = await db.execute(
        select(Response).where(Response.battle_id == battle_id)
    )
    responses = list(result.scalars().all())

    if len(responses) < 2:
        return

    all_done = all(
        (r.content and r.total_latency_ms is not None and r.error is None)
        for r in responses
    )
    any_error = any(r.error is not None for r in responses)

    battle = await db.get(Battle, battle_id)
    if battle is None:
        return

    if any_error:
        battle.status = BattleStatus.failed
    elif all_done:
        battle.status = BattleStatus.ready

    await db.flush()
    await redis.set(f"battle_status:{battle_id}", battle.status.value, ex=3600)
