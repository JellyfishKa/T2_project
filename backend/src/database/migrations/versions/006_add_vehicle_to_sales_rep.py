"""006 add vehicle_id to sales_reps

Revision ID: 006_add_vehicle_to_sales_rep
Revises: 005_add_skipped_stash
Create Date: 2026-04-15
"""
import sqlalchemy as sa
from alembic import op

revision = "006_add_vehicle_to_sales_rep"
down_revision = "005_add_skipped_stash"
branch_labels = None
depends_on = None

VEHICLES_TABLE = "vehicles"
SALES_REPS_TABLE = "sales_reps"
VEHICLE_INDEX_NAME = "ix_vehicles_id"
SALES_REPS_VEHICLE_INDEX_NAME = "ix_sales_reps_vehicle_id"


def _get_tables() -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return set(inspector.get_table_names())


def _get_columns(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def _get_indexes(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {index["name"] for index in inspector.get_indexes(table_name)}


def _has_vehicle_fk() -> bool:
    inspector = sa.inspect(op.get_bind())
    for foreign_key in inspector.get_foreign_keys(SALES_REPS_TABLE):
        if (
            foreign_key.get("referred_table") == VEHICLES_TABLE
            and foreign_key.get("constrained_columns") == ["vehicle_id"]
        ):
            return True
    return False


def _get_vehicle_fk_names() -> list[str]:
    inspector = sa.inspect(op.get_bind())
    names: list[str] = []
    for foreign_key in inspector.get_foreign_keys(SALES_REPS_TABLE):
        if (
            foreign_key.get("referred_table") == VEHICLES_TABLE
            and foreign_key.get("constrained_columns") == ["vehicle_id"]
            and foreign_key.get("name")
        ):
            names.append(foreign_key["name"])
    return names


def upgrade() -> None:
    tables = _get_tables()
    if VEHICLES_TABLE not in tables:
        op.create_table(
            VEHICLES_TABLE,
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("fuel_price_rub", sa.Float(), nullable=False),
            sa.Column("consumption_city_l_100km", sa.Float(), nullable=False),
            sa.Column("consumption_highway_l_100km", sa.Float(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    if VEHICLE_INDEX_NAME not in _get_indexes(VEHICLES_TABLE):
        op.create_index(VEHICLE_INDEX_NAME, VEHICLES_TABLE, ["id"])

    if "vehicle_id" not in _get_columns(SALES_REPS_TABLE):
        op.add_column(
            SALES_REPS_TABLE,
            sa.Column("vehicle_id", sa.String(), nullable=True),
        )

    if not _has_vehicle_fk():
        op.create_foreign_key(
            "fk_sales_reps_vehicle_id_vehicles",
            SALES_REPS_TABLE,
            VEHICLES_TABLE,
            ["vehicle_id"],
            ["id"],
            ondelete="SET NULL",
        )

    if SALES_REPS_VEHICLE_INDEX_NAME not in _get_indexes(SALES_REPS_TABLE):
        op.create_index(
            SALES_REPS_VEHICLE_INDEX_NAME,
            SALES_REPS_TABLE,
            ["vehicle_id"],
        )


def downgrade() -> None:
    if SALES_REPS_VEHICLE_INDEX_NAME in _get_indexes(SALES_REPS_TABLE):
        op.drop_index(SALES_REPS_VEHICLE_INDEX_NAME, table_name=SALES_REPS_TABLE)

    for foreign_key_name in _get_vehicle_fk_names():
        op.drop_constraint(foreign_key_name, SALES_REPS_TABLE, type_="foreignkey")

    if "vehicle_id" in _get_columns(SALES_REPS_TABLE):
        op.drop_column(SALES_REPS_TABLE, "vehicle_id")

    if VEHICLE_INDEX_NAME in _get_indexes(VEHICLES_TABLE):
        op.drop_index(VEHICLE_INDEX_NAME, table_name=VEHICLES_TABLE)

    if VEHICLES_TABLE in _get_tables():
        op.drop_table(VEHICLES_TABLE)
