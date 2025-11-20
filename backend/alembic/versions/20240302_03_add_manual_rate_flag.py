"""add manual flag to exchange rates

Revision ID: 20240302_03
Revises: 20240302_02
Create Date: 2024-03-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20240302_03"
down_revision: Union[str, None] = "20240302_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "exchange_rates",
        sa.Column("is_manual", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("exchange_rates", "is_manual", server_default=None)


def downgrade() -> None:
    op.drop_column("exchange_rates", "is_manual")
