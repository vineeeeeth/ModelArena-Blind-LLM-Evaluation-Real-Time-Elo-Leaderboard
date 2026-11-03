"""Simulate realistic battles and votes from a latent true-strength model."""

from __future__ import annotations

import asyncio
import math
import random
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import numpy as np
from sqlalchemy import select

from app.core.db import async_session_factory
from app.core.logging import logger
from app.models.tables import (
    AnonSession,
    Battle,
    BattleCategory,
    BattleStatus,
    CategorySource,
    Model,
    Response,
    SlotEnum,
    Vote,
    VoteChoice,
)
from app.services.rating_service import compute_full_rankings

# Latent true strengths (on ~Elo scale) per category
TRUE_STRENGTHS = {
    BattleCategory.general: {
        "gpt-4o": 1250,
        "claude-3-haiku": 1180,
        "gemini-1.5-flash": 1170,
        "gpt-4o-mini": 1160,
        "llama-3.2-3b": 1050,
        "qwen-2.5-3b": 1040,
        "phi-3-mini": 990,
        "gemma-2-2b": 980,
    },
    BattleCategory.coding: {
        "gpt-4o": 1280,
        "qwen-2.5-3b": 1140,
        "gpt-4o-mini": 1130,
        "claude-3-haiku": 1120,
        "gemini-1.5-flash": 1100,
        "llama-3.2-3b": 1020,
        "phi-3-mini": 980,
        "gemma-2-2b": 940,
    },
    BattleCategory.math: {
        "gpt-4o": 1270,
        "qwen-2.5-3b": 1160,
        "gpt-4o-mini": 1140,
        "gemini-1.5-flash": 1120,
        "claude-3-haiku": 1100,
        "llama-3.2-3b": 990,
        "phi-3-mini": 970,
        "gemma-2-2b": 960,
    },
    BattleCategory.hindi: {
        "gpt-4o": 1220,
        "gemini-1.5-flash": 1200,
        "llama-3.2-3b": 1080,
        "qwen-2.5-3b": 1070,
        "claude-3-haiku": 1060,
        "gpt-4o-mini": 1050,
        "gemma-2-2b": 960,
        "phi-3-mini": 930,
    },
    BattleCategory.summarization: {
        "gpt-4o": 1240,
        "claude-3-haiku": 1210,
        "gemini-1.5-flash": 1180,
        "gpt-4o-mini": 1150,
        "llama-3.2-3b": 1030,
        "qwen-2.5-3b": 1020,
        "phi-3-mini": 980,
        "gemma-2-2b": 970,
    },
}

SAMPLE_PROMPTS = {
    BattleCategory.general: [
        "Explain quantum computing in simple terms for a 10-year-old.",
        "What are the main causes and effects of the French Revolution?",
        "Write a creative short story about a time traveler who gets stuck in 1999.",
        "How do airplanes stay in the air? Explain the physics principles involved.",
        "Compare stoicism and existentialism in terms of handling personal crises.",
    ],
    BattleCategory.coding: [
        "Write a clean Python function to find the longest palindromic substring in O(n^2) time.",
        "How do I implement a rate limiter using Redis in TypeScript with a sliding window?",
        "Debug this SQL query: SELECT department, COUNT(*) FROM employees GROUP BY department HAVING salary > 50000.",
        "Explain the difference between useEffect and useLayoutEffect in React with code examples.",
        "Write an async pipeline in Rust that reads from a mpsc channel and batches writes to disk.",
    ],
    BattleCategory.math: [
        "Solve the differential equation dy/dx + 2y = 4x with initial condition y(0) = 1.",
        "Compute the integral from 0 to infinity of x^3 * e^(-x) dx.",
        "Prove that the square root of 2 is an irrational number by contradiction.",
        "In a bag of 5 red and 7 blue balls, what is the probability of drawing 2 red balls without replacement?",
        "Explain the intuition behind Bayes' theorem with a disease screening example.",
    ],
    BattleCategory.hindi: [
        "भारतीय संविधान की प्रमुख विशेषताओं का संक्षेप में वर्णन कीजिए।",
        "सूरदास और तुलसीदास की भक्ति काव्य धारा में क्या प्रमुख अंतर हैं?",
        "ग्लोबल वार्मिंग पर 200 शब्दों का एक प्रभावशाली निबंध लिखिए।",
        "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन श्लोक का आधुनिक संदर्भ में क्या अर्थ है?",
        "एक छोटे किसान की दिनचर्या और उसकी समस्याओं पर एक संवेदनशील कहानी लिखिए।",
    ],
    BattleCategory.summarization: [
        "Summarize the key takeaways of the 2024 IPCC Climate Change Report.",
        "Provide a 3-bullet summary of the plot of Hamlet.",
        "Summarize this legal contract terms regarding confidentiality and IP ownership.",
        "TL;DR of the paper 'Attention Is All You Need' focusing on Multi-Head Self-Attention.",
        "Summarize the economic impacts of inflation and high interest rates on middle-class households.",
    ],
}


def sample_outcome(strength_a: float, strength_b: float) -> VoteChoice:
    diff = strength_a - strength_b
    prob_a_wins = 1.0 / (1.0 + math.exp(-diff / 100.0))

    r = random.random()
    tie_prob = 0.08
    both_bad_prob = 0.02

    if r < both_bad_prob:
        return VoteChoice.both_bad
    elif r < both_bad_prob + tie_prob:
        return VoteChoice.tie
    elif r < both_bad_prob + tie_prob + (1.0 - tie_prob - both_bad_prob) * prob_a_wins:
        return VoteChoice.A
    else:
        return VoteChoice.B


async def simulate_battles(num_battles: int = 1500):
    logger.info("simulation_started", target_battles=num_battles)

    async with async_session_factory() as session:
        models_res = await session.execute(select(Model))
        models = list(models_res.scalars().all())
        model_by_slug = {m.slug: m for m in models}

        if len(models) < 2:
            logger.error("not_enough_models_to_simulate")
            return

        # Ensure demo anonymous session
        demo_session_id = uuid.uuid4()
        demo_session = AnonSession(id=demo_session_id)
        session.add(demo_session)
        await session.flush()

        categories = list(BattleCategory)
        now = datetime.now(timezone.utc)

        for i in range(num_battles):
            cat = random.choice(categories)
            prompt = random.choice(SAMPLE_PROMPTS[cat])

            # Pick two distinct models
            m_a, m_b = random.sample(models, 2)

            strengths = TRUE_STRENGTHS.get(cat, {})
            str_a = strengths.get(m_a.slug, 1000)
            str_b = strengths.get(m_b.slug, 1000)

            choice = sample_outcome(str_a, str_b)

            # Stagger timestamps across past 30 days
            created_at = now - timedelta(
                days=random.uniform(0, 30),
                hours=random.uniform(0, 24),
                minutes=random.uniform(0, 60),
            )

            battle = Battle(
                prompt_text=prompt,
                category=cat,
                category_source=CategorySource.auto,
                model_a_id=m_a.id,
                model_b_id=m_b.id,
                session_id=demo_session_id,
                status=BattleStatus.voted,
                created_at=created_at,
            )
            session.add(battle)
            await session.flush()

            # Latencies & tokens
            lat_a = int(random.gauss(1400, 300))
            lat_b = int(random.gauss(1400, 300))
            in_tok = random.randint(20, 100)
            out_tok_a = random.randint(150, 600)
            out_tok_b = random.randint(150, 600)

            cost_a = (Decimal(in_tok) * m_a.input_price_per_mtok + Decimal(out_tok_a) * m_a.output_price_per_mtok) / Decimal(1_000_000)
            cost_b = (Decimal(in_tok) * m_b.input_price_per_mtok + Decimal(out_tok_b) * m_b.output_price_per_mtok) / Decimal(1_000_000)

            resp_a = Response(
                battle_id=battle.id,
                slot=SlotEnum.A,
                model_id=m_a.id,
                content=f"Simulated response from {m_a.display_name} for '{prompt[:40]}...'",
                input_tokens=in_tok,
                output_tokens=out_tok_a,
                ttft_ms=random.randint(150, 450),
                total_latency_ms=max(lat_a, 400),
                cost_usd=cost_a,
                created_at=created_at,
            )
            resp_b = Response(
                battle_id=battle.id,
                slot=SlotEnum.B,
                model_id=m_b.id,
                content=f"Simulated response from {m_b.display_name} for '{prompt[:40]}...'",
                input_tokens=in_tok,
                output_tokens=out_tok_b,
                ttft_ms=random.randint(150, 450),
                total_latency_ms=max(lat_b, 400),
                cost_usd=cost_b,
                created_at=created_at,
            )
            session.add(resp_a)
            session.add(resp_b)

            vote = Vote(
                battle_id=battle.id,
                choice=choice,
                voter_session_id=demo_session_id,
                time_to_vote_ms=random.randint(2500, 12000),
                is_simulated=True,
                created_at=created_at,
            )
            session.add(vote)

            if (i + 1) % 100 == 0:
                await session.commit()
                logger.info("simulated_chunk", count=i + 1)

        await session.commit()
        logger.info("simulation_persisted")

        # Now compute all rankings
        logger.info("computing_rankings_after_simulation")
        await compute_full_rankings(session, category=None, include_simulated=True)
        for cat in BattleCategory:
            await compute_full_rankings(session, category=cat, include_simulated=True)

        logger.info("simulation_pipeline_complete")


if __name__ == "__main__":
    asyncio.run(simulate_battles(1200))

