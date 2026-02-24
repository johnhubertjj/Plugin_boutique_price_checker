"""Initial production schema for API, auth, and worker tables."""

from alembic import op
import sqlalchemy as sa

revision = "20260212_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("phone_number", sa.String(length=32), nullable=True),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("phone_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("two_factor_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_id", "users", ["id"], unique=False)

    op.create_table(
        "watchlist_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("product_url", sa.Text(), nullable=False),
        sa.Column("threshold", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_price", sa.Float(), nullable=True),
        sa.Column("last_currency", sa.String(length=4), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_watchlist_items_id", "watchlist_items", ["id"], unique=False)
    op.create_index("ix_watchlist_items_user_id", "watchlist_items", ["user_id"], unique=False)

    op.create_table(
        "price_check_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("watchlist_item_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("price_amount", sa.Float(), nullable=True),
        sa.Column("price_currency", sa.String(length=4), nullable=True),
        sa.Column("alert_sent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["watchlist_item_id"], ["watchlist_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_price_check_runs_id", "price_check_runs", ["id"], unique=False)
    op.create_index("ix_price_check_runs_watchlist_item_id", "price_check_runs", ["watchlist_item_id"], unique=False)

    op.create_table(
        "auth_codes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("purpose", sa.String(length=32), nullable=False),
        sa.Column("channel", sa.String(length=16), nullable=False),
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_auth_codes_id", "auth_codes", ["id"], unique=False)
    op.create_index("ix_auth_codes_purpose", "auth_codes", ["purpose"], unique=False)
    op.create_index("ix_auth_codes_user_id", "auth_codes", ["user_id"], unique=False)

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_auth_sessions_id", "auth_sessions", ["id"], unique=False)
    op.create_index("ix_auth_sessions_token_hash", "auth_sessions", ["token_hash"], unique=True)
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"], unique=False)

    op.create_table(
        "otp_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("subject_key", sa.String(length=512), nullable=False),
        sa.Column("fail_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("blocked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_otp_attempts_id", "otp_attempts", ["id"], unique=False)
    op.create_index("ix_otp_attempts_subject_key", "otp_attempts", ["subject_key"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_otp_attempts_subject_key", table_name="otp_attempts")
    op.drop_index("ix_otp_attempts_id", table_name="otp_attempts")
    op.drop_table("otp_attempts")

    op.drop_index("ix_auth_sessions_user_id", table_name="auth_sessions")
    op.drop_index("ix_auth_sessions_token_hash", table_name="auth_sessions")
    op.drop_index("ix_auth_sessions_id", table_name="auth_sessions")
    op.drop_table("auth_sessions")

    op.drop_index("ix_auth_codes_user_id", table_name="auth_codes")
    op.drop_index("ix_auth_codes_purpose", table_name="auth_codes")
    op.drop_index("ix_auth_codes_id", table_name="auth_codes")
    op.drop_table("auth_codes")

    op.drop_index("ix_price_check_runs_watchlist_item_id", table_name="price_check_runs")
    op.drop_index("ix_price_check_runs_id", table_name="price_check_runs")
    op.drop_table("price_check_runs")

    op.drop_index("ix_watchlist_items_user_id", table_name="watchlist_items")
    op.drop_index("ix_watchlist_items_id", table_name="watchlist_items")
    op.drop_table("watchlist_items")

    op.drop_index("ix_users_id", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

