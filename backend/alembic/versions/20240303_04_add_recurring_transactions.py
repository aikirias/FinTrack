"""add recurring_transactions table and composite index on transactions

Revision ID: 20240303_04
Revises: 20240302_03
Create Date: 2024-03-03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20240303_04"
down_revision: Union[str, None] = "20240302_03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Composite index on transactions for range queries
    op.create_index(
        "ix_transactions_user_date",
        "transactions",
        ["user_id", "transaction_date"],
    )

    op.create_table(
        "recurring_transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("subcategory_id", sa.Integer(), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("amount_original", sa.Numeric(20, 8), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column("rate_type", sa.String(length=20), nullable=False, server_default="official"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("frequency", sa.String(length=20), nullable=False),
        sa.Column("next_run_date", sa.Date(), nullable=False),
        sa.Column("last_run_date", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_recurring_transactions_user_id", "recurring_transactions", ["user_id"])
    op.create_index("ix_recurring_transactions_next_run_date", "recurring_transactions", ["next_run_date"])


def downgrade() -> None:
    op.drop_index("ix_recurring_transactions_next_run_date", table_name="recurring_transactions")
    op.drop_index("ix_recurring_transactions_user_id", table_name="recurring_transactions")
    op.drop_table("recurring_transactions")
    op.drop_index("ix_transactions_user_date", table_name="transactions")
