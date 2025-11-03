"""Initial schema

Revision ID: 20240225_01
Revises: 
Create Date: 2024-02-25 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import column, table


# revision identifiers, used by Alembic.
revision: str = "20240225_01"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


CATEGORY_TYPE = sa.Enum("income", "expense", "transfer", name="categorytype")


def upgrade() -> None:
    op.create_table(
        "currencies",
        sa.Column("code", sa.String(length=3), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("symbol", sa.String(length=8), nullable=True),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "exchange_rate_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
        sa.Column("base_url", sa.Text(), nullable=True),
        sa.Column("last_status", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "exchange_rates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("exchange_rate_sources.id"), nullable=True),
        sa.Column("usd_ars_oficial", sa.Numeric(20, 6), nullable=False),
        sa.Column("usd_ars_blue", sa.Numeric(20, 6), nullable=True),
        sa.Column("btc_usd", sa.Numeric(20, 8), nullable=False),
        sa.Column("btc_ars", sa.Numeric(20, 8), nullable=False),
        sa.Column("metadata_payload", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("effective_date", "source_id", name="uq_rate_date_source"),
    )

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("type", CATEGORY_TYPE, nullable=False),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("categories.id", ondelete="CASCADE"), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "name", "parent_id", name="uq_category_name"),
    )
    op.create_index("ix_categories_user_id", "categories", ["user_id"])

    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("currency_code", sa.String(length=3), sa.ForeignKey("currencies.code"), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_accounts_user_id", "accounts", ["user_id"])

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id"), nullable=True),
        sa.Column("subcategory_id", sa.Integer(), sa.ForeignKey("categories.id"), nullable=True),
        sa.Column("exchange_rate_id", sa.Integer(), sa.ForeignKey("exchange_rates.id"), nullable=True),
        sa.Column("transaction_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column("rate_type", sa.String(length=20), nullable=False, server_default="official"),
        sa.Column("amount_original", sa.Numeric(20, 8), nullable=False),
        sa.Column("amount_ars", sa.Numeric(20, 8), nullable=False),
        sa.Column("amount_usd", sa.Numeric(20, 8), nullable=False),
        sa.Column("amount_btc", sa.Numeric(20, 8), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"])
    op.create_index("ix_transactions_date", "transactions", ["transaction_date"])

    # Seed currencies
    op.bulk_insert(
        table(
            "currencies",
            column("code", sa.String(length=3)),
            column("name", sa.String(length=100)),
            column("symbol", sa.String(length=8)),
        ),
        [
            {"code": "ARS", "name": "Peso Argentino", "symbol": "$"},
            {"code": "USD", "name": "Dólar estadounidense", "symbol": "USD"},
            {"code": "BTC", "name": "Bitcoin", "symbol": "BTC"},
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_transactions_date", table_name="transactions")
    op.drop_index("ix_transactions_user_id", table_name="transactions")
    op.drop_table("transactions")
    op.drop_index("ix_accounts_user_id", table_name="accounts")
    op.drop_table("accounts")
    op.drop_index("ix_categories_user_id", table_name="categories")
    op.drop_table("categories")
    op.drop_table("exchange_rates")
    op.drop_table("exchange_rate_sources")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.drop_table("currencies")
    CATEGORY_TYPE.drop(op.get_bind(), checkfirst=False)
