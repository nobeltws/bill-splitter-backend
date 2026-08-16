"""create claims table

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-16 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "claims",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("participant_name", sa.String(100), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], ondelete="CASCADE"),
        sa.CheckConstraint("quantity > 0", name="ck_claims_quantity_positive"),
        sa.UniqueConstraint("session_id", "item_id", "participant_name", name="uq_claims_session_item_participant"),
    )
    op.create_index("ix_claims_session_id", "claims", ["session_id"])
    op.create_index("ix_claims_item_id", "claims", ["item_id"])


def downgrade() -> None:
    op.drop_index("ix_claims_item_id", table_name="claims")
    op.drop_index("ix_claims_session_id", table_name="claims")
    op.drop_table("claims")
