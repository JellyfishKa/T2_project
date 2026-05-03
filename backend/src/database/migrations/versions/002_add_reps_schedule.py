"""002_add_reps_schedule

Revision ID: 002_add_reps_schedule
Revises: 29d28e6d902c
Create Date: 2026-02-26 00:00:00.000000

Добавляет:
- Колонки category, city, district, address в таблицу locations
- Таблицы sales_reps, visit_schedule, visit_log, force_majeure_events
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '002_add_reps_schedule'
down_revision: Union[str, Sequence[str], None] = '29d28e6d902c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Расширение таблицы locations ---
    op.add_column('locations', sa.Column('category', sa.String(1), nullable=True))
    op.add_column('locations', sa.Column('city', sa.String(255), nullable=True))
    op.add_column('locations', sa.Column('district', sa.String(255), nullable=True))
    op.add_column('locations', sa.Column('address', sa.String(500), nullable=True))

    # --- Новая таблица sales_reps ---
    op.create_table(
        'sales_reps',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_sales_reps_id'), 'sales_reps', ['id'], unique=False)

    # --- Новая таблица visit_schedule ---
    op.create_table(
        'visit_schedule',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('location_id', sa.String(), nullable=False),
        sa.Column('rep_id', sa.String(), nullable=False),
        sa.Column('planned_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='planned'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id']),
        sa.ForeignKeyConstraint(['rep_id'], ['sales_reps.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_visit_schedule_id'), 'visit_schedule', ['id'], unique=False)
    op.create_index(op.f('ix_visit_schedule_location_id'), 'visit_schedule',
                    ['location_id'], unique=False)
    op.create_index(op.f('ix_visit_schedule_rep_id'), 'visit_schedule',
                    ['rep_id'], unique=False)
    op.create_index(op.f('ix_visit_schedule_planned_date'), 'visit_schedule',
                    ['planned_date'], unique=False)

    # --- Новая таблица visit_log ---
    op.create_table(
        'visit_log',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('schedule_id', sa.String(), nullable=True),
        sa.Column('location_id', sa.String(), nullable=False),
        sa.Column('rep_id', sa.String(), nullable=False),
        sa.Column('visited_date', sa.Date(), nullable=False),
        sa.Column('time_in', sa.Time(), nullable=True),
        sa.Column('time_out', sa.Time(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id']),
        sa.ForeignKeyConstraint(['rep_id'], ['sales_reps.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['schedule_id'], ['visit_schedule.id'],
                                ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_visit_log_id'), 'visit_log', ['id'], unique=False)
    op.create_index(op.f('ix_visit_log_location_id'), 'visit_log',
                    ['location_id'], unique=False)
    op.create_index(op.f('ix_visit_log_rep_id'), 'visit_log',
                    ['rep_id'], unique=False)
    op.create_index(op.f('ix_visit_log_visited_date'), 'visit_log',
                    ['visited_date'], unique=False)
    op.create_index(op.f('ix_visit_log_schedule_id'), 'visit_log',
                    ['schedule_id'], unique=False)

    # --- Новая таблица force_majeure_events ---
    op.create_table(
        'force_majeure_events',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('rep_id', sa.String(), nullable=False),
        sa.Column('event_date', sa.Date(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('affected_tt_ids', sa.JSON(), nullable=True),
        sa.Column('redistributed_to', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['rep_id'], ['sales_reps.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_force_majeure_events_id'), 'force_majeure_events',
                    ['id'], unique=False)
    op.create_index(op.f('ix_force_majeure_events_rep_id'), 'force_majeure_events',
                    ['rep_id'], unique=False)
    op.create_index(op.f('ix_force_majeure_events_event_date'),
                    'force_majeure_events', ['event_date'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_force_majeure_events_event_date'),
                  table_name='force_majeure_events')
    op.drop_index(op.f('ix_force_majeure_events_rep_id'),
                  table_name='force_majeure_events')
    op.drop_index(op.f('ix_force_majeure_events_id'),
                  table_name='force_majeure_events')
    op.drop_table('force_majeure_events')

    op.drop_index(op.f('ix_visit_log_schedule_id'), table_name='visit_log')
    op.drop_index(op.f('ix_visit_log_visited_date'), table_name='visit_log')
    op.drop_index(op.f('ix_visit_log_rep_id'), table_name='visit_log')
    op.drop_index(op.f('ix_visit_log_location_id'), table_name='visit_log')
    op.drop_index(op.f('ix_visit_log_id'), table_name='visit_log')
    op.drop_table('visit_log')

    op.drop_index(op.f('ix_visit_schedule_planned_date'), table_name='visit_schedule')
    op.drop_index(op.f('ix_visit_schedule_rep_id'), table_name='visit_schedule')
    op.drop_index(op.f('ix_visit_schedule_location_id'), table_name='visit_schedule')
    op.drop_index(op.f('ix_visit_schedule_id'), table_name='visit_schedule')
    op.drop_table('visit_schedule')

    op.drop_index(op.f('ix_sales_reps_id'), table_name='sales_reps')
    op.drop_table('sales_reps')

    op.drop_column('locations', 'address')
    op.drop_column('locations', 'district')
    op.drop_column('locations', 'city')
    op.drop_column('locations', 'category')
