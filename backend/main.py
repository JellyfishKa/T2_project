import logging
import os
import shutil
from contextlib import asynccontextmanager
from datetime import date

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Base, Holiday, VisitLog, engine, get_session
from src.middleware.main import AdvancedMiddleware
from src.routes.benchmark import router as benchmark_router
from src.routes.export import router as export_router
from src.routes.import_excel import router as import_router
from src.routes.force_majeure import router as force_majeure_router
from src.routes.insights import router as insights_router
from src.routes.llama import router as llama_router
from src.routes.locations import router as locations_router
from src.routes.metrics import router as metrics_router
from src.routes.optimize import router as optimize_router
from src.routes.qwen import router as qwen_router
from src.routes.reps import router as reps_router
from src.routes.routing import router as routing_router
from src.routes.routes import router as routes_router
from src.routes.schedule import router as schedule_router
from src.routes.holidays import router as holidays_router
from src.routes.visits import router as visits_router
from src.routes.cruddata import (
    location_router_crud,
    sales_rep_router_crud,
    visit_schedule_router_crud,
    daily_route_router_crud,
    visit_log_router_crud,
    force_majeure_router_crud,
    skipped_visit_router_crud,
    route_router_crud,
    metric_router_crud,
    optimization_router_crud,
    holiday_router_crud,
    audit_log_router_crud,
    vehicle_router_crud,
)

import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up: Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Добавляем колонку model_used если её нет (для существующих БД)
        try:
            await conn.execute(text(
                "ALTER TABLE routes ADD COLUMN IF NOT EXISTS "
                "model_used VARCHAR DEFAULT 'unknown'"
            ))
            logger.info("Column routes.model_used ensured.")
        except Exception as e:
            logger.warning(f"Could not alter routes table: {e}")
        # Добавляем новые колонки в locations если их нет
        for col_def in [
            "category VARCHAR(1)",
            "city VARCHAR(255)",
            "district VARCHAR(255)",
            "address VARCHAR(500)",
        ]:
            col_name = col_def.split()[0]
            try:
                await conn.execute(text(
                    f"ALTER TABLE locations ADD COLUMN IF NOT EXISTS {col_def}"
                ))
            except Exception as e:
                logger.warning(f"Could not add column locations.{col_name}: {e}")
    # Сидирование праздников 2026 (если таблица пуста)
    try:
        from sqlalchemy import text as sql_text
        from src.services.schedule_planner import HOLIDAYS_2026
        from src.database.models import new_session
        async with new_session() as session:
            count_result = await session.execute(sql_text("SELECT COUNT(*) FROM holidays"))
            count = count_result.scalar() or 0
            if count == 0:
                for h_date, h_name in HOLIDAYS_2026:
                    session.add(Holiday(date=h_date, name=h_name, is_working=False))
                await session.commit()
                logger.info("Сидировано %d праздников 2026.", len(HOLIDAYS_2026))
            else:
                logger.info("Таблица holidays уже содержит %d записей, сидирование пропущено.", count)
    except Exception as e:
        logger.warning("Не удалось сидировать праздники: %s", e)

    yield
    logger.info("Shutting down: Closing database engine...")
    await engine.dispose()

app = FastAPI(
    title="T2 Logistics API",
    version="1.2.0",
    lifespan=lifespan,
)

app.add_middleware(AdvancedMiddleware)

cors_origins = os.getenv("CORS_ORIGINS", "").strip()
if cors_origins:
    allowed_origins = [o.strip() for o in cors_origins.split(",")]
else:
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost",
        "http://100.120.184.98",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(locations_router)
api_v1_router.include_router(optimize_router)
api_v1_router.include_router(qwen_router)
api_v1_router.include_router(llama_router)
api_v1_router.include_router(metrics_router)
api_v1_router.include_router(benchmark_router)
api_v1_router.include_router(insights_router)
api_v1_router.include_router(routes_router)
api_v1_router.include_router(routing_router)
# Новые роутеры (Фаза 4–8)
api_v1_router.include_router(reps_router)
api_v1_router.include_router(schedule_router)
api_v1_router.include_router(force_majeure_router)
api_v1_router.include_router(visits_router)
api_v1_router.include_router(export_router)
api_v1_router.include_router(import_router)
api_v1_router.include_router(holidays_router)
# crud
api_v1_router.include_router(location_router_crud)
api_v1_router.include_router(sales_rep_router_crud)
api_v1_router.include_router(visit_schedule_router_crud)
api_v1_router.include_router(daily_route_router_crud)
api_v1_router.include_router(visit_log_router_crud)
api_v1_router.include_router(force_majeure_router_crud)
api_v1_router.include_router(skipped_visit_router_crud)
api_v1_router.include_router(route_router_crud)
api_v1_router.include_router(metric_router_crud)
api_v1_router.include_router(optimization_router_crud)
api_v1_router.include_router(holiday_router_crud)
api_v1_router.include_router(audit_log_router_crud)
api_v1_router.include_router(vehicle_router_crud)

app.include_router(api_v1_router)


async def _health_response(session: AsyncSession):
    """Общая логика health check — используется двумя эндпоинтами."""
    try:
        await session.execute(text("SELECT 1"))
        from src.models.qwen_client import QwenClient
        from src.models.llama_client import LlamaClient
        qwen_loaded = QwenClient._llm is not None
        llama_loaded = LlamaClient._llm is not None

        # Disk free (в MB)
        try:
            disk = shutil.disk_usage("/")
            disk_free_mb = round(disk.free / 1024 / 1024)
        except Exception:
            disk_free_mb = None

        # Визиты за сегодня
        try:
            today = date.today()
            visits_result = await session.execute(
                select(func.count()).where(VisitLog.visited_date == today)
            )
            visits_today = visits_result.scalar() or 0
        except Exception:
            visits_today = None

        return {
            "status": "healthy",
            "database": "connected",
            "services": {
                "database": "connected",
                "qwen": "loaded" if qwen_loaded else "not_loaded",
                "llama": "loaded" if llama_loaded else "not_loaded",
            },
            "disk_free_mb": disk_free_mb,
            "visits_today": visits_today,
            "version": "1.2.0",
        }
    except Exception as exc:
        logger.error(f"Health check failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "services": {
                    "database": "disconnected",
                    "qwen": "error",
                    "llama": "error",
                },
            },
        )


@app.get("/health", tags=["System"], status_code=status.HTTP_200_OK)
async def health_check(session: AsyncSession = Depends(get_session)):
    """Health check — для Docker и прямых обращений."""
    return await _health_response(session)


@api_v1_router.get("/health", tags=["System"], status_code=status.HTTP_200_OK)
async def health_check_v1(session: AsyncSession = Depends(get_session)):
    """Health check — для фронтенда (GET /api/v1/health)."""
    return await _health_response(session)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
