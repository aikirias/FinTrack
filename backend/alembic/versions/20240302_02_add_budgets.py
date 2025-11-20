"""add budgets tables

Revision ID: 20240302_02
Revises: 20240225_01
Create Date: 2024-03-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20240302_02"
down_revision: Union[str, None] = "20240225_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "budgets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("currency_code", sa.String(length=3), sa.ForeignKey("currencies.code"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_budgets_user_id", "budgets", ["user_id"])
    op.create_index("ix_budgets_month", "budgets", ["month"])
    op.create_unique_constraint("uq_budget_month_currency", "budgets", ["user_id", "month", "currency_code"])

    op.create_table(
        "budget_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("budget_id", sa.Integer(), sa.ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.Numeric(20, 2), nullable=False),
    )
    op.create_index("ix_budget_items_budget_id", "budget_items", ["budget_id"])
    op.create_index("ix_budget_items_category_id", "budget_items", ["category_id"])


def downgrade() -> None:
    op.drop_index("ix_budget_items_category_id", table_name="budget_items")
    op.drop_index("ix_budget_items_budget_id", table_name="budget_items")
    op.drop_table("budget_items")

    op.drop_constraint("uq_budget_month_currency", "budgets", type_="unique")
    op.drop_index("ix_budgets_month", table_name="budgets")
    op.drop_index("ix_budgets_user_id", table_name="budgets")
    op.drop_table("budgets")
