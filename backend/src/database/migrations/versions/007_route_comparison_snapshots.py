"""007 route comparison snapshots

Revision ID: 007_route_comparison_snapshots
Revises: 006_add_vehicle_to_sales_rep
Create Date: 2026-04-22
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

revision = "007_route_comparison_snapshots"
down_revision = "006_add_vehicle_to_sales_rep"
branch_labels = None
depends_on = None

TABLE_NAME = "optimization_results"
ROUTE_INDEX_NAME = "ix_optimization_results_route_id"
ROUTE_FK_NAME = "fk_optimization_results_route_id_routes"
SNAPSHOT_COLUMNS: Sequence[tuple[str, sa.types.TypeEngine]] = (
    ("original_distance_km", sa.Float()),
    ("original_time_hours", sa.Float()),
    ("original_cost_rub", sa.Float()),
    ("optimized_distance_km", sa.Float()),
    ("optimized_time_hours", sa.Float()),
    ("optimized_cost_rub", sa.Float()),
)


def _get_columns() -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(TABLE_NAME)}


def _get_indexes() -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {index["name"] for index in inspector.get_indexes(TABLE_NAME)}


def _has_route_fk() -> bool:
    inspector = sa.inspect(op.get_bind())
    for foreign_key in inspector.get_foreign_keys(TABLE_NAME):
        if (
            foreign_key.get("referred_table") == "routes"
            and foreign_key.get("constrained_columns") == ["route_id"]
        ):
            return True
    return False


def _get_route_fk_names() -> list[str]:
    inspector = sa.inspect(op.get_bind())
    names: list[str] = []
    for foreign_key in inspector.get_foreign_keys(TABLE_NAME):
        if (
            foreign_key.get("referred_table") == "routes"
            and foreign_key.get("constrained_columns") == ["route_id"]
            and foreign_key.get("name")
        ):
            names.append(foreign_key["name"])
    return names


def upgrade() -> None:
    columns = _get_columns()

    if "route_id" not in columns:
        op.add_column(TABLE_NAME, sa.Column("route_id", sa.String(), nullable=True))
        columns.add("route_id")

    for column_name, column_type in SNAPSHOT_COLUMNS:
        if column_name not in columns:
            op.add_column(TABLE_NAME, sa.Column(column_name, column_type, nullable=True))

    if not _has_route_fk():
        op.create_foreign_key(
            ROUTE_FK_NAME,
            TABLE_NAME,
            "routes",
            ["route_id"],
            ["id"],
            ondelete="SET NULL",
        )

    if ROUTE_INDEX_NAME not in _get_indexes():
        op.create_index(ROUTE_INDEX_NAME, TABLE_NAME, ["route_id"])


def downgrade() -> None:
    indexes = _get_indexes()
    if ROUTE_INDEX_NAME in indexes:
        op.drop_index(ROUTE_INDEX_NAME, table_name=TABLE_NAME)

    for foreign_key_name in _get_route_fk_names():
        op.drop_constraint(foreign_key_name, TABLE_NAME, type_="foreignkey")

    columns = _get_columns()
    for column_name, _ in reversed(SNAPSHOT_COLUMNS):
        if column_name in columns:
            op.drop_column(TABLE_NAME, column_name)

    columns = _get_columns()
    if "route_id" in columns:
        op.drop_column(TABLE_NAME, "route_id")
