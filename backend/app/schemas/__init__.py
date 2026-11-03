"""Pydantic v2 schemas for ModelArena API."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Auth ──


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str
    is_email_verified: bool
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Models ──


class ModelResponse(BaseModel):
    id: int
    slug: str
    display_name: str
    provider: str
    is_open_source: bool
    is_enabled: bool
    input_price_per_mtok: Decimal
    output_price_per_mtok: Decimal

    model_config = {"from_attributes": True}


class ModelAdminUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    input_price_per_mtok: Optional[Decimal] = None
    output_price_per_mtok: Optional[Decimal] = None


# ── Battle ──


class BattleCreateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)
    category: Optional[str] = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str | None) -> str | None:
        if v is not None:
            allowed = {"general", "coding", "math", "hindi", "summarization"}
            if v.lower() not in allowed:
                raise ValueError(f"Category must be one of {allowed}")
            return v.lower()
        return v


class BattleCreatedResponse(BaseModel):
    battle_id: uuid.UUID
    category: str


class VoteRequest(BaseModel):
    choice: str = Field(pattern="^(A|B|tie|both_bad)$")
    time_to_vote_ms: Optional[int] = None


class ResponseReveal(BaseModel):
    slot: str
    model_name: str
    model_slug: str
    input_tokens: int
    output_tokens: int
    ttft_ms: Optional[int]
    total_latency_ms: Optional[int]
    cost_usd: float


class VoteResultResponse(BaseModel):
    choice: str
    responses: list[ResponseReveal]


class BattleStatusResponse(BaseModel):
    battle_id: uuid.UUID
    status: str
    category: str
    prompt: str


# ── Leaderboard ──


class LeaderboardEntry(BaseModel):
    model_id: int
    model_slug: str
    model_name: str
    provider: str
    is_open_source: bool
    elo: float
    bt_score: float
    ci_low: float
    ci_high: float
    rank: int
    num_battles: int
    win_rate: float
    avg_latency_ms: float
    avg_cost_usd: float
    is_provisional: bool = False

    model_config = {"from_attributes": True}


class LeaderboardResponse(BaseModel):
    category: Optional[str]
    entries: list[LeaderboardEntry]
    includes_simulated: bool = True
    computed_at: Optional[datetime] = None


# ── Stats ──


class PairwiseEntry(BaseModel):
    model_a_slug: str
    model_b_slug: str
    a_wins: int
    b_wins: int
    ties: int
    total: int
    a_win_rate: float


class WinMatrixResponse(BaseModel):
    category: Optional[str]
    model_slugs: list[str]
    matrix: list[list[Optional[float]]]


class ModelStatsResponse(BaseModel):
    slug: str
    display_name: str
    provider: str
    categories: dict[str, LeaderboardEntry]


class TrendPoint(BaseModel):
    computed_at: datetime
    elo: float
    bt_score: float


class TrendResponse(BaseModel):
    model_slug: str
    category: Optional[str]
    points: list[TrendPoint]


class CostLatencyPoint(BaseModel):
    model_slug: str
    model_name: str
    avg_cost_usd: float
    avg_latency_ms: float
    elo: float


# ── Health ──


class HealthResponse(BaseModel):
    status: str
    db: str
    redis: str
    ollama: str

