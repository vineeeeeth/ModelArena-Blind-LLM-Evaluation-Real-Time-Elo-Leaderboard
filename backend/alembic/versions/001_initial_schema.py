"""Initial schema creation

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-03 20:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Create Enums ──
    user_role_enum = postgresql.ENUM("user", "admin", name="userrole", create_type=False)
    user_role_enum.create(op.get_bind(), checkfirst=True)

    category_enum = postgresql.ENUM(
        "general", "coding", "math", "hindi", "summarization", name="battlecategory", create_type=False
    )
    category_enum.create(op.get_bind(), checkfirst=True)

    category_source_enum = postgresql.ENUM("auto", "user", name="categorysource", create_type=False)
    category_source_enum.create(op.get_bind(), checkfirst=True)

    status_enum = postgresql.ENUM("generating", "ready", "voted", "failed", name="battlestatus", create_type=False)
    status_enum.create(op.get_bind(), checkfirst=True)

    slot_enum = postgresql.ENUM("A", "B", name="slotenum", create_type=False)
    slot_enum.create(op.get_bind(), checkfirst=True)

    vote_choice_enum = postgresql.ENUM("A", "B", "tie", "both_bad", name="votechoice", create_type=False)
    vote_choice_enum.create(op.get_bind(), checkfirst=True)

    # ── Users ──
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=True),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("is_email_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("role", user_role_enum, nullable=False, server_default="user"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── OAuth Accounts ──
    op.create_table(
        "oauth_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("provider_account_id", sa.String(255), nullable=False),
        sa.UniqueConstraint("provider", "provider_account_id", name="uq_oauth_provider_account"),
    )

    # ── Email Verification Tokens ──
    op.create_table(
        "email_verification_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── Password Reset Tokens ──
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── Refresh Tokens ──
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("ip", sa.String(45), nullable=True),
    )

    # ── Anon Sessions ──
    op.create_table(
        "anon_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )

    # ── Models ──
    op.create_table(
        "models",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("provider_model_id", sa.String(200), nullable=False),
        sa.Column("input_price_per_mtok", sa.Numeric(10, 4), nullable=False, server_default="0"),
        sa.Column("output_price_per_mtok", sa.Numeric(10, 4), nullable=False, server_default="0"),
        sa.Column("is_open_source", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── Battles ──
    op.create_table(
        "battles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("prompt_text", sa.Text(), nullable=False),
        sa.Column("category", category_enum, nullable=False),
        sa.Column("category_source", category_source_enum, nullable=False, server_default="auto"),
        sa.Column("model_a_id", sa.Integer(), sa.ForeignKey("models.id"), nullable=False),
        sa.Column("model_b_id", sa.Integer(), sa.ForeignKey("models.id"), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("anon_sessions.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", status_enum, nullable=False, server_default="generating"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("model_a_id != model_b_id", name="ck_different_models"),
    )
    op.create_index("ix_battles_category_created", "battles", ["category", "created_at"])

    # ── Responses ──
    op.create_table(
        "responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("battle_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("battles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("slot", slot_enum, nullable=False),
        sa.Column("model_id", sa.Integer(), sa.ForeignKey("models.id"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ttft_ms", sa.Integer(), nullable=True),
        sa.Column("total_latency_ms", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(12, 8), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("battle_id", "slot", name="uq_response_battle_slot"),
    )
    op.create_index("ix_responses_model_id", "responses", ["model_id"])

    # ── Votes ──
    op.create_table(
        "votes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("battle_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("battles.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("choice", vote_choice_enum, nullable=False),
        sa.Column("voter_session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("anon_sessions.id"), nullable=False),
        sa.Column("voter_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("time_to_vote_ms", sa.Integer(), nullable=True),
        sa.Column("is_simulated", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_votes_created_at", "votes", ["created_at"])

    # ── Rating Snapshots ──
    op.create_table(
        "rating_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("model_id", sa.Integer(), sa.ForeignKey("models.id"), nullable=False),
        sa.Column("elo", sa.Numeric(10, 2), nullable=False, server_default="1000"),
        sa.Column("bt_score", sa.Numeric(10, 2), nullable=False, server_default="1000"),
        sa.Column("ci_low", sa.Numeric(10, 2), nullable=False, server_default="1000"),
        sa.Column("ci_high", sa.Numeric(10, 2), nullable=False, server_default="1000"),
        sa.Column("rank", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("num_battles", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("win_rate", sa.Numeric(5, 4), nullable=False, server_default="0"),
        sa.Column("avg_latency_ms", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("avg_cost_usd", sa.Numeric(12, 8), nullable=False, server_default="0"),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_rating_snapshots_cat_computed", "rating_snapshots", ["category", "computed_at"])

    # ── Pairwise Stats ──
    op.create_table(
        "pairwise_stats",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("model_a_id", sa.Integer(), sa.ForeignKey("models.id"), nullable=False),
        sa.Column("model_b_id", sa.Integer(), sa.ForeignKey("models.id"), nullable=False),
        sa.Column("a_wins", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("b_wins", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ties", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("category", "model_a_id", "model_b_id", name="uq_pairwise"),
    )


def downgrade() -> None:
    op.drop_table("pairwise_stats")
    op.drop_table("rating_snapshots")
    op.drop_table("votes")
    op.drop_table("responses")
    op.drop_table("battles")
    op.drop_table("models")
    op.drop_table("anon_sessions")
    op.drop_table("refresh_tokens")
    op.drop_table("password_reset_tokens")
    op.drop_table("email_verification_tokens")
    op.drop_table("oauth_accounts")
    op.drop_table("users")

