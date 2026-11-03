"""Tests for Elo, Bradley-Terry MLE, and Bootstrap Confidence Intervals."""

import math
import pytest
from app.models.tables import VoteChoice
from app.services.rating_service import (
    compute_online_elo,
    fit_bradley_terry,
    bootstrap_bradley_terry_ci,
    _expected_score,
)


def test_elo_hand_computed_example():
    """
    Test standard Elo computation with K=32.
    Player A: 1000, Player B: 1000.
    Expected win rate = 0.5.
    If A wins:
        A new = 1000 + 32 * (1.0 - 0.5) = 1016.0
        B new = 1000 + 32 * (0.0 - 0.5) = 984.0
    """
    new_a, new_b = compute_online_elo(1000.0, 1000.0, VoteChoice.A, k=32.0)
    assert new_a == 1016.0
    assert new_b == 984.0


def test_elo_tie_calculation():
    """
    Test Elo tie outcome:
    Player A: 1000, Player B: 1000.
    Both expected 0.5. Actual score 0.5.
    No change in ratings.
    """
    new_a, new_b = compute_online_elo(1000.0, 1000.0, VoteChoice.tie, k=32.0)
    assert new_a == 1000.0
    assert new_b == 1000.0


def test_elo_both_bad_ignored():
    """
    'Both bad' votes must NOT alter ratings.
    """
    new_a, new_b = compute_online_elo(1050.0, 950.0, VoteChoice.both_bad)
    assert new_a == 1050.0
    assert new_b == 950.0


def test_bradley_terry_recovery_of_known_strengths():
    """
    Simulate matches between 3 models with known abilities:
    Model 1: strong (1200)
    Model 2: medium (1000)
    Model 3: weak (800)
    BT MLE must recover Model 1 > Model 2 > Model 3.
    """
    model_ids = [1, 2, 3]
    battles_data = []

    # Model 1 beats Model 2 70% of the time
    for _ in range(70):
        battles_data.append((1, 2, 1.0))
    for _ in range(30):
        battles_data.append((1, 2, 0.0))

    # Model 2 beats Model 3 70% of the time
    for _ in range(70):
        battles_data.append((2, 3, 1.0))
    for _ in range(30):
        battles_data.append((2, 3, 0.0))

    # Model 1 beats Model 3 90% of the time
    for _ in range(90):
        battles_data.append((1, 3, 1.0))
    for _ in range(10):
        battles_data.append((1, 3, 0.0))

    scores = fit_bradley_terry(model_ids, battles_data)

    assert scores[1] > scores[2], f"Model 1 ({scores[1]}) should beat Model 2 ({scores[2]})"
    assert scores[2] > scores[3], f"Model 2 ({scores[2]}) should beat Model 3 ({scores[3]})"


def test_bootstrap_confidence_intervals():
    """
    Bootstrap CIs must produce valid lower and upper bounds: ci_low <= score <= ci_high.
    """
    model_ids = [10, 20]
    battles_data = []
    for _ in range(40):
        battles_data.append((10, 20, 1.0))
    for _ in range(20):
        battles_data.append((10, 20, 0.0))

    ci_dict = bootstrap_bradley_terry_ci(model_ids, battles_data, n_bootstraps=50)

    for m_id in model_ids:
        low, high = ci_dict[m_id]
        assert low <= high, f"CI lower bound {low} must be <= upper bound {high}"

