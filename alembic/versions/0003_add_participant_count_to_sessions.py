"""add participant_count to sessions

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-16 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, Sequence[str], None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sessions", sa.Column("participant_count", sa.Integer(), nullable=False, server_default="1"))
    op.create_check_constraint("ck_sessions_participant_count_positive", "sessions", "participant_count > 0")


def downgrade() -> None:
    op.drop_constraint("ck_sessions_participant_count_positive", "sessions")
    op.drop_column("sessions", "participant_count")
