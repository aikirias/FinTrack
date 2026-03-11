"""add transfer_pair_id and transfer_direction to transactions

Revision ID: 20240304_05
Revises: 20240303_04
Create Date: 2024-03-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20240304_05"
down_revision: Union[str, None] = "20240303_04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("transactions", sa.Column("transfer_pair_id", sa.Integer(), nullable=True))
    op.add_column("transactions", sa.Column("transfer_direction", sa.String(3), nullable=True))
    op.create_foreign_key(
        "fk_transactions_transfer_pair",
        "transactions",
        "transactions",
        ["transfer_pair_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_transactions_transfer_pair_id", "transactions", ["transfer_pair_id"])


def downgrade() -> None:
    op.drop_index("ix_transactions_transfer_pair_id", table_name="transactions")
    op.drop_constraint("fk_transactions_transfer_pair", "transactions", type_="foreignkey")
    op.drop_column("transactions", "transfer_direction")
    op.drop_column("transactions", "transfer_pair_id")
