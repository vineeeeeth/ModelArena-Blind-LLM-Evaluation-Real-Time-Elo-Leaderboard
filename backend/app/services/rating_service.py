"""Rating service – Online Elo, Bradley-Terry MLE, and Bootstrap Confidence Intervals."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from typing import Any, Optional

import numpy as np
from scipy.optimize import minimize
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.core.redis import redis
from app.models.tables import Battle, BattleCategory, BattleStatus, Model, PairwiseStats, RatingSnapshot, Vote, VoteChoice

K_FACTOR = 32.0
INITIAL_ELO = 1000.0
MIN_BATTLES_PROVISIONAL = 20
SCALE_FACTOR = 400.0 / math.log(10.0)  # ~173.7177 to scale logistic regression to Elo-scale


def _expected_score(rating_a: float, rating_b: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))


def compute_online_elo(
    current_a: float,
    current_b: float,
    choice: VoteChoice,
    k: float = K_FACTOR,
) -> tuple[float, float]:
    """Calculate new Elo scores given current ratings and a match outcome."""
    if choice == VoteChoice.both_bad:
        return current_a, current_b

    exp_a = _expected_score(current_a, current_b)
    exp_b = 1.0 - exp_a

    if choice == VoteChoice.A:
        act_a, act_b = 1.0, 0.0
    elif choice == VoteChoice.B:
        act_a, act_b = 0.0, 1.0
    elif choice == VoteChoice.tie:
        act_a, act_b = 0.5, 0.5
    else:
        return current_a, current_b

    new_a = current_a + k * (act_a - exp_a)
    new_b = current_b + k * (act_b - exp_b)
    return round(new_a, 2), round(new_b, 2)


async def update_online_elo_vote(
    db: AsyncSession,
    battle: Battle,
    vote: Vote,
) -> None:
    """Updates Redis cached Elo after a vote immediately."""
    if vote.choice == VoteChoice.both_bad:
        return

    cat_key_a = f"elo:{battle.category.value}:{battle.model_a_id}"
    cat_key_b = f"elo:{battle.category.value}:{battle.model_b_id}"
    overall_key_a = f"elo:overall:{battle.model_a_id}"
    overall_key_b = f"elo:overall:{battle.model_b_id}"

    # Fetch existing or fallback to 1000.0
    val_a = await redis.get(cat_key_a)
    val_b = await redis.get(cat_key_b)
    curr_cat_a = float(val_a) if val_a else INITIAL_ELO
    curr_cat_b = float(val_b) if val_b else INITIAL_ELO

    new_cat_a, new_cat_b = compute_online_elo(curr_cat_a, curr_cat_b, vote.choice)
    await redis.set(cat_key_a, str(new_cat_a))
    await redis.set(cat_key_b, str(new_cat_b))

    val_ov_a = await redis.get(overall_key_a)
    val_ov_b = await redis.get(overall_key_b)
    curr_ov_a = float(val_ov_a) if val_ov_a else INITIAL_ELO
    curr_ov_b = float(val_ov_b) if val_ov_b else INITIAL_ELO

    new_ov_a, new_ov_b = compute_online_elo(curr_ov_a, curr_ov_b, vote.choice)
    await redis.set(overall_key_a, str(new_ov_a))
    await redis.set(overall_key_b, str(new_ov_b))


def fit_bradley_terry(
    model_ids: list[int],
    battles_data: list[tuple[int, int, float]],
) -> dict[int, float]:
    """
    Fits Bradley-Terry model using MLE via negative log-likelihood minimization.
    battles_data is a list of (model_a_id, model_b_id, score_a) where score_a is 1.0 (A win), 0.0 (B win), 0.5 (tie).
    Returns dict of model_id -> score (centered with mean = 1000 on Elo-like scale).
    """
    n_models = len(model_ids)
    if n_models == 0:
        return {}
    if n_models == 1:
        return {model_ids[0]: INITIAL_ELO}

    id_to_idx = {m_id: idx for idx, m_id in enumerate(model_ids)}

    # Negative log-likelihood function
    # gamma = log(ability). Anchor gamma[0] = 0 for identifiability
    def neg_log_likelihood(params: np.ndarray) -> float:
        # params length is n_models - 1 (params[0] is fixed at 0)
        gamma = np.zeros(n_models)
        gamma[1:] = params

        nll = 0.0
        for m_a, m_b, s_a in battles_data:
            idx_a, idx_b = id_to_idx[m_a], id_to_idx[m_b]
            diff = gamma[idx_a] - gamma[idx_b]
            # p_a = 1 / (1 + exp(-diff)) = sigmoid(diff)
            # log(p_a) = diff - log(1 + exp(diff)) = -log(1 + exp(-diff))
            # log(1 - p_a) = -diff - log(1 + exp(-diff))
            # numerically stable log(1 + exp(x)) = np.logaddexp(0, x)
            log_p_a = -np.logaddexp(0, -diff)
            log_p_b = -np.logaddexp(0, diff)

            if s_a == 1.0:
                nll -= log_p_a
            elif s_a == 0.0:
                nll -= log_p_b
            elif s_a == 0.5:
                # ties count as 0.5 win for each
                nll -= 0.5 * (log_p_a + log_p_b)
        
        # L2 regularization for stability
        nll += 0.01 * np.sum(params ** 2)
        return float(nll)

    init_params = np.zeros(n_models - 1)
    res = minimize(neg_log_likelihood, init_params, method="L-BFGS-B")
    
    final_gamma = np.zeros(n_models)
    if res.success:
        final_gamma[1:] = res.x

    # Scale to Elo: Elo = INITIAL_ELO + SCALE_FACTOR * (gamma - mean(gamma))
    centered_gamma = final_gamma - np.mean(final_gamma)
    elo_scores = INITIAL_ELO + SCALE_FACTOR * centered_gamma

    return {m_id: round(float(elo_scores[id_to_idx[m_id]]), 2) for m_id in model_ids}


def bootstrap_bradley_terry_ci(
    model_ids: list[int],
    battles_data: list[tuple[int, int, float]],
    n_bootstraps: int = 200,
) -> dict[int, tuple[float, float]]:
    """
    Resamples battles with replacement and refits Bradley-Terry to calculate 95% CIs.
    Returns dict of model_id -> (ci_low, ci_high).
    """
    n_battles = len(battles_data)
    if n_battles < 5 or len(model_ids) < 2:
        return {m_id: (INITIAL_ELO, INITIAL_ELO) for m_id in model_ids}

    bootstrap_scores: dict[int, list[float]] = {m_id: [] for m_id in model_ids}

    # Pre-convert to numpy array for fast sampling
    data_indices = np.arange(n_battles)

    for _ in range(n_bootstraps):
        sampled_indices = np.random.choice(data_indices, size=n_battles, replace=True)
        sampled_data = [battles_data[i] for i in sampled_indices]
        scores = fit_bradley_terry(model_ids, sampled_data)
        for m_id in model_ids:
            bootstrap_scores[m_id].append(scores.get(m_id, INITIAL_ELO))

    ci_dict: dict[int, tuple[float, float]] = {}
    for m_id in model_ids:
        arr = np.array(bootstrap_scores[m_id])
        low = float(np.percentile(arr, 2.5))
        high = float(np.percentile(arr, 97.5))
        ci_dict[m_id] = (round(low, 2), round(high, 2))

    return ci_dict


async def compute_full_rankings(
    db: AsyncSession,
    category: Optional[BattleCategory] = None,
    include_simulated: bool = True,
) -> list[RatingSnapshot]:
    """
    Computes Elo, Bradley-Terry scores, and Bootstrap CIs for the given category (or overall).
    Saves snapshots to DB and caches in Redis.
    """
    # 1. Fetch enabled models
    models_res = await db.execute(select(Model).where(Model.is_enabled.is_(True)))
    models = list(models_res.scalars().all())
    if not models:
        return []

    model_ids = [m.id for m in models]
    model_map = {m.id: m for m in models}

    # 2. Fetch all battles with votes
    query = (
        select(Battle.model_a_id, Battle.model_b_id, Vote.choice, Battle.id)
        .join(Vote, Battle.id == Vote.battle_id)
        .where(Battle.status == BattleStatus.voted)
    )
    if category is not None:
        query = query.where(Battle.category == category)
    if not include_simulated:
        query = query.where(Vote.is_simulated.is_(False))

    votes_res = await db.execute(query)
    rows = votes_res.all()

    battles_data: list[tuple[int, int, float]] = []
    # For stats
    battle_counts: dict[int, int] = {m_id: 0 for m_id in model_ids}
    wins: dict[int, float] = {m_id: 0.0 for m_id in model_ids}
    pairwise_wins: dict[tuple[int, int], int] = {}
    pairwise_ties: dict[tuple[int, int], int] = {}

    for m_a, m_b, choice, _ in rows:
        if m_a not in model_map or m_b not in model_map:
            continue
        battle_counts[m_a] += 1
        battle_counts[m_b] += 1

        score_a = None
        if choice == VoteChoice.A:
            score_a = 1.0
            wins[m_a] += 1.0
            pair = (min(m_a, m_b), max(m_a, m_b))
            pairwise_wins[(m_a, m_b)] = pairwise_wins.get((m_a, m_b), 0) + 1
        elif choice == VoteChoice.B:
            score_a = 0.0
            wins[m_b] += 1.0
            pairwise_wins[(m_b, m_a)] = pairwise_wins.get((m_b, m_a), 0) + 1
        elif choice == VoteChoice.tie:
            score_a = 0.5
            wins[m_a] += 0.5
            wins[m_b] += 0.5
            pair = (min(m_a, m_b), max(m_a, m_b))
            pairwise_ties[pair] = pairwise_ties.get(pair, 0) + 1
        elif choice == VoteChoice.both_bad:
            continue

        if score_a is not None:
            battles_data.append((m_a, m_b, score_a))

    # 3. Fit Bradley-Terry & Compute Bootstrap CI
    bt_scores = fit_bradley_terry(model_ids, battles_data)
    ci_scores = bootstrap_bradley_terry_ci(model_ids, battles_data, n_bootstraps=200)

    # 4. Fetch Response performance metrics (latency, cost)
    from app.models.tables import Response
    resp_query = (
        select(
            Response.model_id,
            func.avg(Response.total_latency_ms),
            func.avg(Response.cost_usd),
        )
        .group_by(Response.model_id)
    )
    resp_res = await db.execute(resp_query)
    perf_metrics = {r[0]: (float(r[1] or 0), float(r[2] or 0)) for r in resp_res.all()}

    # 5. Calculate CI-aware ranks
    # A model's rank upper bound = 1 + count of models whose CI lower bound is above its CI upper bound
    cat_str = category.value if category else None
    snapshots: list[RatingSnapshot] = []

    # Sort models primarily by bt_score descending
    sorted_model_ids = sorted(model_ids, key=lambda m_id: bt_scores.get(m_id, INITIAL_ELO), reverse=True)

    for rank_idx, m_id in enumerate(sorted_model_ids, start=1):
        bt = bt_scores.get(m_id, INITIAL_ELO)
        ci_l, ci_h = ci_scores.get(m_id, (INITIAL_ELO, INITIAL_ELO))
        b_count = battle_counts.get(m_id, 0)
        w_rate = (wins.get(m_id, 0.0) / b_count) if b_count > 0 else 0.0
        avg_lat, avg_cost = perf_metrics.get(m_id, (0.0, 0.0))

        # Online Elo fallback from Redis or snapshot
        redis_elo_val = await redis.get(f"elo:{cat_str or 'overall'}:{m_id}")
        elo_val = float(redis_elo_val) if redis_elo_val else bt

        snapshot = RatingSnapshot(
            category=cat_str,
            model_id=m_id,
            elo=elo_val,
            bt_score=bt,
            ci_low=ci_l,
            ci_high=ci_h,
            rank=rank_idx,
            num_battles=b_count,
            win_rate=round(w_rate, 4),
            avg_latency_ms=round(avg_lat, 2),
            avg_cost_usd=round(avg_cost, 8),
            computed_at=datetime.now(timezone.utc),
        )
        snapshots.append(snapshot)
        db.add(snapshot)

    await db.commit()

    # 6. Cache leaderboard in Redis for fast serving
    cache_payload = [
        {
            "model_id": s.model_id,
            "model_slug": model_map[s.model_id].slug,
            "model_name": model_map[s.model_id].display_name,
            "provider": model_map[s.model_id].provider,
            "is_open_source": model_map[s.model_id].is_open_source,
            "elo": float(s.elo),
            "bt_score": float(s.bt_score),
            "ci_low": float(s.ci_low),
            "ci_high": float(s.ci_high),
            "rank": s.rank,
            "num_battles": s.num_battles,
            "win_rate": float(s.win_rate),
            "avg_latency_ms": float(s.avg_latency_ms),
            "avg_cost_usd": float(s.avg_cost_usd),
            "is_provisional": s.num_battles < MIN_BATTLES_PROVISIONAL,
        }
        for s in snapshots
    ]
    cache_key = f"leaderboard:{cat_str or 'overall'}:sim_{include_simulated}"
    await redis.set(cache_key, json.dumps(cache_payload), ex=300)

    # 7. Update PairwiseStats
    for (m_a, m_b), a_w in pairwise_wins.items():
        b_w = pairwise_wins.get((m_b, m_a), 0)
        pair = (min(m_a, m_b), max(m_a, m_b))
        t_count = pairwise_ties.get(pair, 0)
        
        # update or insert
        stmt = select(PairwiseStats).where(
            PairwiseStats.category == cat_str,
            PairwiseStats.model_a_id == m_a,
            PairwiseStats.model_b_id == m_b,
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            existing.a_wins = a_w
            existing.b_wins = b_w
            existing.ties = t_count
        else:
            db.add(PairwiseStats(
                category=cat_str,
                model_a_id=m_a,
                model_b_id=m_b,
                a_wins=a_w,
                b_wins=b_w,
                ties=t_count,
            ))
    await db.commit()

    return snapshots

