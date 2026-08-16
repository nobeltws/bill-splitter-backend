"""rename tax and service_charge to rates

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-16 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, Sequence[str], None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("sessions", "tax", new_column_name="tax_rate", type_=sa.Numeric(5, 4), server_default="0.09")
    op.alter_column("sessions", "service_charge", new_column_name="service_charge_rate", type_=sa.Numeric(5, 4), server_default="0.10")


def downgrade() -> None:
    op.alter_column("sessions", "tax_rate", new_column_name="tax", type_=sa.Numeric(10, 2), server_default="0")
    op.alter_column("sessions", "service_charge_rate", new_column_name="service_charge", type_=sa.Numeric(10, 2), server_default="0")
