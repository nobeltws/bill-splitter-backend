"""create payments table

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-16 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: Union[str, Sequence[str], None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("participant_name", sa.String(100), nullable=False),
        sa.Column("paid_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("session_id", "participant_name", name="uq_payments_session_participant"),
    )
    op.create_index("ix_payments_session_id", "payments", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_payments_session_id", table_name="payments")
    op.drop_table("payments")
