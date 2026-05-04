import os
import uuid
from datetime import UTC, datetime, timezone

from dotenv import load_dotenv

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Float,
    ForeignKey, Index, Integer, JSON, String, Text, Time, UniqueConstraint)
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base, relationship


load_dotenv()

DATABASE_URL = (
    f"postgresql+asyncpg://{os.getenv('DATABASE_USER', 'postgres')}:"
    f"{os.getenv('DATABASE_PASSWORD', 'postgres')}@"
    f"{os.getenv('DATABASE_HOST', 'localhost')}:"
    f"{os.getenv('DATABASE_PORT', '5432')}/"
    f"{os.getenv('DATABASE_NAME', 't2')}"
)

engine = create_async_engine(DATABASE_URL)
new_session = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()


async def get_session():
    async with new_session() as session:
        yield session


class Location(Base):
    """SQLAlchemy model for store locations."""
    __tablename__ = "locations"

    id = Column(String, primary_key=True, index=True,
                default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    time_window_start = Column(String, nullable=False)
    time_window_end = Column(String, nullable=False)
    # Новые поля (Фаза 1)
    category = Column(String(1), nullable=True)   # A | B | C | D
    city = Column(String(255), nullable=True)
    district = Column(String(255), nullable=True)  # Саранск, Ардатовский р-н, …
    address = Column(String(500), nullable=True)

    def __repr__(self):
        return f"<Location(id={self.id}, name={self.name}, category={self.category})>"


class SalesRep(Base):
    """Торговый представитель."""
    __tablename__ = "sales_reps"

    id = Column(String, primary_key=True, index=True,
                default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="active")
    # active | sick | vacation | unavailable
    vehicle_id = Column(String, ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))

    vehicle = relationship("Vehicle", foreign_keys=[vehicle_id])
    schedules = relationship("VisitSchedule", back_populates="rep",
                             cascade="all, delete-orphan")
    visits = relationship("VisitLog", back_populates="rep",
                          cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SalesRep(id={self.id}, name={self.name}, status={self.status})>"


class VisitSchedule(Base):
    """Плановый визит торгового представителя к ТТ."""
    __tablename__ = "visit_schedule"
    __table_args__ = (
        Index("ix_visit_schedule_rep_date_status", "rep_id", "planned_date", "status"),
    )

    id = Column(String, primary_key=True, index=True,
                default=lambda: str(uuid.uuid4()))
    location_id = Column(String, ForeignKey("locations.id"), nullable=False, index=True)
    rep_id = Column(String, ForeignKey("sales_reps.id", ondelete="CASCADE"),
                    nullable=False, index=True)
    planned_date = Column(Date, nullable=False, index=True)
    status = Column(String, nullable=False, default="planned")
    # planned | completed | skipped | rescheduled | cancelled
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))

    location = relationship("Location")
    rep = relationship("SalesRep", back_populates="schedules")
    visit_log = relationship("VisitLog", back_populates="schedule",
                             cascade="all, delete-orphan")

    def __repr__(self):
        return (f"<VisitSchedule(rep={self.rep_id}, loc={self.location_id},"
                f" date={self.planned_date}, status={self.status})>")


class DailyRouteOverride(Base):
    """Переопределение порядка точек для конкретного сотрудника и дня."""
    __tablename__ = "daily_route_overrides"
    __table_args__ = (
        UniqueConstraint("rep_id", "route_date", name="uq_daily_route_override_rep_date"),
    )

    id = Column(String, primary_key=True, index=True,
                default=lambda: str(uuid.uuid4()))
    rep_id = Column(String, ForeignKey("sales_reps.id", ondelete="CASCADE"),
                    nullable=False, index=True)
    route_date = Column(Date, nullable=False, index=True)
    original_location_order = Column(JSON, nullable=False, default=list)
    current_location_order = Column(JSON, nullable=False, default=list)
    source = Column(String, nullable=False, default="manual")
    label = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    rep = relationship("SalesRep")

    def __repr__(self):
        return (f"<DailyRouteOverride(rep={self.rep_id}, date={self.route_date}, "
                f"source={self.source})>")


class VisitLog(Base):
    """Фактический визит торгового представителя к ТТ."""
    __tablename__ = "visit_log"

    id = Column(String, primary_key=True, index=True,
                default=lambda: str(uuid.uuid4()))
    schedule_id = Column(String, ForeignKey("visit_schedule.id", ondelete="SET NULL"),
                         nullable=True, index=True)
    location_id = Column(String, ForeignKey("locations.id"), nullable=False, index=True)
    rep_id = Column(String, ForeignKey("sales_reps.id", ondelete="CASCADE"),
                    nullable=False, index=True)
    visited_date = Column(Date, nullable=False, index=True)
    time_in = Column(Time, nullable=True)
    time_out = Column(Time, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))

    schedule = relationship("VisitSchedule", back_populates="visit_log")
    location = relationship("Location")
    rep = relationship("SalesRep", back_populates="visits")

    def __repr__(self):
        return (f"<VisitLog(rep={self.rep_id}, loc={self.location_id},"
                f" date={self.visited_date})>")


class ForceMajeureEvent(Base):
    """Форс-мажорное событие с перераспределением ТТ."""
    __tablename__ = "force_majeure_events"

    id = Column(String, primary_key=True, index=True,
                default=lambda: str(uuid.uuid4()))
    type = Column(String, nullable=False)
    # illness | weather | vehicle_breakdown | other
    rep_id = Column(String, ForeignKey("sales_reps.id", ondelete="CASCADE"),
                    nullable=False, index=True)
    event_date = Column(Date, nullable=False, index=True)
    description = Column(Text, nullable=True)
    affected_tt_ids = Column(JSON, default=list)
    redistributed_to = Column(JSON, default=list)
    return_time = Column(Time, nullable=True)
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))

    rep = relationship("SalesRep")

    def __repr__(self):
        return (f"<ForceMajeureEvent(type={self.type}, rep={self.rep_id},"
                f" date={self.event_date})>")


class SkippedVisitStash(Base):
    """Стеш пропущенных визитов, ожидающих перераспределения."""
    __tablename__ = "skipped_visit_stash"

    id = Column(String, primary_key=True, index=True,
                default=lambda: str(uuid.uuid4()))
    visit_schedule_id = Column(
        String, ForeignKey("visit_schedule.id", ondelete="SET NULL"), nullable=True
    )
    location_id = Column(
        String, ForeignKey("locations.id"), nullable=False, index=True
    )
    rep_id = Column(
        String, ForeignKey("sales_reps.id", ondelete="CASCADE"), nullable=False, index=True
    )
    original_date = Column(Date, nullable=False, index=True)
    resolution = Column(String, nullable=True)  # manual | ai | carry_over | NULL = pending
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_schedule_id = Column(
        String, ForeignKey("visit_schedule.id", ondelete="SET NULL"), nullable=True
    )
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))

    location = relationship("Location")
    rep = relationship("SalesRep")

    def __repr__(self):
        return (f"<SkippedVisitStash(rep={self.rep_id}, loc={self.location_id},"
                f" date={self.original_date}, resolution={self.resolution})>")


class Route(Base):
    """SQLAlchemy model for logistics routes."""
    __tablename__ = "routes"

    id = Column(String, primary_key=True, index=True,
                default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    locations_order = Column(JSON, nullable=False)
    total_distance = Column(Float, nullable=False)
    total_time = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    model_used = Column(String, nullable=False, default="unknown")
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))

    metrics = relationship("Metric", back_populates="route",
                           cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Route(id={self.id}, name={self.name})>"


class Metric(Base):
    """SQLAlchemy model for tracking AI model performance metrics."""
    __tablename__ = "metrics"

    id = Column(String, primary_key=True, index=True,
                default=lambda: str(uuid.uuid4()))
    route_id = Column(String, ForeignKey("routes.id",
                                         ondelete="CASCADE"), index=True)
    model_name = Column(String, nullable=False, index=True)
    response_time_ms = Column(Integer, nullable=False)
    quality_score = Column(Float, nullable=False)
    cost = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True),
                       default=lambda: datetime.now(timezone.utc))

    route = relationship("Route", back_populates="metrics")

    def __repr__(self):
        return f"<Metric(model={self.model_name}, score={self.quality_score})>"


class OptimizationResult(Base):
    """SQLAlchemy model for storing optimization comparison results."""
    __tablename__ = "optimization_results"

    id = Column(String, primary_key=True, index=True,
                default=lambda: str(uuid.uuid4()))
    route_id = Column(String, ForeignKey("routes.id", ondelete="SET NULL"),
                      nullable=True, index=True)
    original_route = Column(JSON, nullable=False)
    optimized_route = Column(JSON, nullable=False)
    original_distance_km = Column(Float, nullable=True)
    original_time_hours = Column(Float, nullable=True)
    original_cost_rub = Column(Float, nullable=True)
    optimized_distance_km = Column(Float, nullable=True)
    optimized_time_hours = Column(Float, nullable=True)
    optimized_cost_rub = Column(Float, nullable=True)
    improvement_percentage = Column(Float, nullable=False)
    model_used = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))

    route = relationship("Route")

    def __repr__(self):
        return "<OptimizationResult(imp={self.improvement_percentage}%)>"


class Holiday(Base):
    """Праздничный день с возможностью ручного управления статусом."""
    __tablename__ = "holidays"

    date = Column(Date, primary_key=True)
    name = Column(Text, nullable=False)
    is_working = Column(Boolean, nullable=False, default=False)
    # False = нерабочий (дефолт), True = рабочий (переопределён пользователем)

    def __repr__(self):
        return f"<Holiday(date={self.date}, name={self.name}, is_working={self.is_working})>"


class AuditLog(Base):
    """Журнал изменений — логирует ключевые действия в системе."""
    __tablename__ = "audit_log"

    id = Column(String, primary_key=True, index=True,
                default=lambda: str(uuid.uuid4()))
    action = Column(String, nullable=False)
    # "visit_status_change" | "force_majeure_created" | "schedule_generated"
    table_name = Column(String, nullable=True)
    record_id = Column(String, nullable=True)
    old_value = Column(Text, nullable=True)   # JSON string
    new_value = Column(Text, nullable=True)   # JSON string
    details = Column(Text, nullable=True)     # JSON string, доп. контекст
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(UTC))

    def __repr__(self):
        return f"<AuditLog(action={self.action}, table={self.table_name}, record={self.record_id})>"

class Vehicle(Base):
    """Транспортные средства — содержит информацию об автомобилях."""
    __tablename__ = "vehicles"

    id = Column(String, primary_key=True, index=True,
                default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    fuel_price_rub = Column(Float, nullable=False)                 # Стоимость 1 литра топлива
    consumption_city_l_100km = Column(Float, nullable=False)       # Расход в городе (л/100 км)
    consumption_highway_l_100km = Column(Float, nullable=False)    # Расход на трассе (л/100 км)
