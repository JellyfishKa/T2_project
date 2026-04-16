"""006 add vehicle_id to sales_reps

Revision ID: 006_add_vehicle_to_sales_rep
Revises: 005_add_skipped_stash
Create Date: 2026-04-15
"""
from alembic import op
import sqlalchemy as sa

revision = "006_add_vehicle_to_sales_rep"
down_revision = "005_add_skipped_stash"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sales_reps",
        sa.Column(
            "vehicle_id",
            sa.String(),
            sa.ForeignKey("vehicles.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_sales_reps_vehicle_id", "sales_reps", ["vehicle_id"])


def downgrade() -> None:
    op.drop_index("ix_sales_reps_vehicle_id", table_name="sales_reps")
    op.drop_column("sales_reps", "vehicle_id")
