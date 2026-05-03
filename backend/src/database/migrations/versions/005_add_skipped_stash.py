"""005_add_skipped_stash

Revision ID: 005_add_skipped_stash
Revises: 004_add_fm_return_time
Create Date: 2026-04-13 00:00:00.000000

Добавляет:
- Таблицу skipped_visit_stash для хранения пропущенных визитов,
  ожидающих ручного перераспределения (manual/ai/carry_over)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005_add_skipped_stash"
down_revision: Union[str, None] = "004_add_fm_return_time"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "skipped_visit_stash",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("visit_schedule_id", sa.String(), nullable=True),
        sa.Column("location_id", sa.String(), nullable=False),
        sa.Column("rep_id", sa.String(), nullable=False),
        sa.Column("original_date", sa.Date(), nullable=False),
        sa.Column("resolution", sa.String(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_schedule_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["location_id"], ["locations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["rep_id"], ["sales_reps.id"], ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["visit_schedule_id"], ["visit_schedule.id"], ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["resolved_schedule_id"], ["visit_schedule.id"], ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_skipped_stash_location_id", "skipped_visit_stash", ["location_id"])
    op.create_index("ix_skipped_stash_rep_id", "skipped_visit_stash", ["rep_id"])
    op.create_index("ix_skipped_stash_original_date", "skipped_visit_stash", ["original_date"])


def downgrade() -> None:
    op.drop_index("ix_skipped_stash_original_date", table_name="skipped_visit_stash")
    op.drop_index("ix_skipped_stash_rep_id", table_name="skipped_visit_stash")
    op.drop_index("ix_skipped_stash_location_id", table_name="skipped_visit_stash")
    op.drop_table("skipped_visit_stash")
