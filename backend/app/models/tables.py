"""SQLAlchemy ORM models for ModelArena."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Enums ──


class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"


class BattleCategory(str, enum.Enum):
    general = "general"
    coding = "coding"
    math = "math"
    hindi = "hindi"
    summarization = "summarization"


class CategorySource(str, enum.Enum):
    auto = "auto"
    user = "user"


class BattleStatus(str, enum.Enum):
    generating = "generating"
    ready = "ready"
    voted = "voted"
    failed = "failed"


class SlotEnum(str, enum.Enum):
    A = "A"
    B = "B"


class VoteChoice(str, enum.Enum):
    A = "A"
    B = "B"
    tie = "tie"
    both_bad = "both_bad"


# ── Users ──


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.user, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    oauth_accounts: Mapped[list[OAuthAccount]] = relationship(back_populates="user", cascade="all, delete-orphan")
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(back_populates="user", cascade="all, delete-orphan")


class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"
    __table_args__ = (UniqueConstraint("provider", "provider_account_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_account_id: Mapped[str] = mapped_column(String(255), nullable=False)

    user: Mapped[User] = relationship(back_populates="oauth_accounts")


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)

    user: Mapped[User] = relationship(back_populates="refresh_tokens")


# ── Anonymous sessions ──


class AnonSession(Base):
    __tablename__ = "anon_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


# ── Models (LLM registry) ──


class Model(Base):
    __tablename__ = "models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # ollama, openai, anthropic, gemini
    provider_model_id: Mapped[str] = mapped_column(String(200), nullable=False)
    input_price_per_mtok: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0, nullable=False)
    output_price_per_mtok: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0, nullable=False)
    is_open_source: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)


# ── Battles ──


class Battle(Base):
    __tablename__ = "battles"
    __table_args__ = (
        CheckConstraint("model_a_id != model_b_id", name="ck_different_models"),
        Index("ix_battles_category_created", "category", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[BattleCategory] = mapped_column(Enum(BattleCategory), nullable=False)
    category_source: Mapped[CategorySource] = mapped_column(Enum(CategorySource), default=CategorySource.auto, nullable=False)
    model_a_id: Mapped[int] = mapped_column(ForeignKey("models.id"), nullable=False)
    model_b_id: Mapped[int] = mapped_column(ForeignKey("models.id"), nullable=False)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("anon_sessions.id"), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[BattleStatus] = mapped_column(Enum(BattleStatus), default=BattleStatus.generating, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    model_a: Mapped[Model] = relationship(foreign_keys=[model_a_id])
    model_b: Mapped[Model] = relationship(foreign_keys=[model_b_id])
    responses: Mapped[list[Response]] = relationship(back_populates="battle", cascade="all, delete-orphan")
    vote: Mapped[Vote | None] = relationship(back_populates="battle", uselist=False)


# ── Responses ──


class Response(Base):
    __tablename__ = "responses"
    __table_args__ = (
        UniqueConstraint("battle_id", "slot", name="uq_response_battle_slot"),
        Index("ix_responses_model_id", "model_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    battle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("battles.id", ondelete="CASCADE"), nullable=False)
    slot: Mapped[SlotEnum] = mapped_column(Enum(SlotEnum), nullable=False)
    model_id: Mapped[int] = mapped_column(ForeignKey("models.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ttft_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(12, 8), default=0, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    battle: Mapped[Battle] = relationship(back_populates="responses")


# ── Votes ──


class Vote(Base):
    __tablename__ = "votes"
    __table_args__ = (
        Index("ix_votes_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    battle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("battles.id", ondelete="CASCADE"), unique=True, nullable=False)
    choice: Mapped[VoteChoice] = mapped_column(Enum(VoteChoice), nullable=False)
    voter_session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("anon_sessions.id"), nullable=False)
    voter_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    time_to_vote_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    battle: Mapped[Battle] = relationship(back_populates="vote")


# ── Rating snapshots ──


class RatingSnapshot(Base):
    __tablename__ = "rating_snapshots"
    __table_args__ = (
        Index("ix_rating_snapshots_cat_computed", "category", "computed_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)  # None = overall
    model_id: Mapped[int] = mapped_column(ForeignKey("models.id"), nullable=False)
    elo: Mapped[float] = mapped_column(Numeric(10, 2), default=1000, nullable=False)
    bt_score: Mapped[float] = mapped_column(Numeric(10, 2), default=1000, nullable=False)
    ci_low: Mapped[float] = mapped_column(Numeric(10, 2), default=1000, nullable=False)
    ci_high: Mapped[float] = mapped_column(Numeric(10, 2), default=1000, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    num_battles: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    win_rate: Mapped[float] = mapped_column(Numeric(5, 4), default=0, nullable=False)
    avg_latency_ms: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    avg_cost_usd: Mapped[float] = mapped_column(Numeric(12, 8), default=0, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    model: Mapped[Model] = relationship()


# ── Pairwise stats ──


class PairwiseStats(Base):
    __tablename__ = "pairwise_stats"
    __table_args__ = (
        UniqueConstraint("category", "model_a_id", "model_b_id", name="uq_pairwise"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model_a_id: Mapped[int] = mapped_column(ForeignKey("models.id"), nullable=False)
    model_b_id: Mapped[int] = mapped_column(ForeignKey("models.id"), nullable=False)
    a_wins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    b_wins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ties: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

