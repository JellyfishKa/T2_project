import os
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv

from sqlalchemy import (
    Column, DateTime, Float,
    ForeignKey, Integer, JSON, String)
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base, relationship


load_dotenv()

DATABASE_URL = (
    f"postgresql+asyncpg://{os.getenv('DATABASE_USER', 'postgres')}:"
    f"{os.getenv('DATABASE_PASSWORD', 'postgres')}@"
    f"{os.getenv('DATABASE_HOST', 'localhost')}/"
    f"{os.getenv('DATABASE_NAME', 'postgres')}"
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

    def __repr__(self):
        return f"<Location(id={self.id}, name={self.name})>"


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
