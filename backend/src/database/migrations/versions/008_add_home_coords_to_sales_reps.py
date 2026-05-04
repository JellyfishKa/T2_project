"""008 add home coords to sales reps

Revision ID: 008_add_home_coords_to_sales_reps
Revises: 007_route_comparison_snapshots
Create Date: 2026-05-04
"""

from alembic import op
import sqlalchemy as sa

revision = "008_add_home_coords_to_sales_reps"
down_revision = "007_route_comparison_snapshots"
branch_labels = None
depends_on = None

TABLE_NAME = "sales_reps"


def _get_columns() -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(TABLE_NAME)}


def upgrade() -> None:
    columns = _get_columns()
    if "home_lat" not in columns:
        op.add_column(
            TABLE_NAME,
            sa.Column(
                "home_lat",
                sa.Float(),
                nullable=False,
                server_default="54.1871",
            ),
        )
    if "home_lon" not in columns:
        op.add_column(
            TABLE_NAME,
            sa.Column(
                "home_lon",
                sa.Float(),
                nullable=False,
                server_default="45.1749",
            ),
        )


def downgrade() -> None:
    columns = _get_columns()
    if "home_lon" in columns:
        op.drop_column(TABLE_NAME, "home_lon")
    if "home_lat" in columns:
        op.drop_column(TABLE_NAME, "home_lat")
