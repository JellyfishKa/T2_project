import os
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv

from sqlalchemy import (
    Column, Date, DateTime, Float,
    ForeignKey, Integer, JSON, String, Text, Time)
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
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))

    schedules = relationship("VisitSchedule", back_populates="rep",
                             cascade="all, delete-orphan")
    visits = relationship("VisitLog", back_populates="rep",
                          cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SalesRep(id={self.id}, name={self.name}, status={self.status})>"


class VisitSchedule(Base):
    """Плановый визит торгового представителя к ТТ."""
    __tablename__ = "visit_schedule"

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
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))

    rep = relationship("SalesRep")

    def __repr__(self):
        return (f"<ForceMajeureEvent(type={self.type}, rep={self.rep_id},"
                f" date={self.event_date})>")


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
    original_route = Column(JSON, nullable=False)
    optimized_route = Column(JSON, nullable=False)
    improvement_percentage = Column(Float, nullable=False)
    model_used = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return "<OptimizationResult(imp={self.improvement_percentage}%)>"
