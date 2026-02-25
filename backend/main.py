import logging
import os
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Base, engine, get_session
from src.middleware.main import AdvancedMiddleware
from src.routes.benchmark import router as benchmark_router
from src.routes.insights import router as insights_router
from src.routes.llama import router as llama_router
from src.routes.locations import router as locations_router
from src.routes.metrics import router as metrics_router
from src.routes.optimize import router as optimize_router
from src.routes.qwen import router as qwen_router
from src.routes.routes import router as routes_router

import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up: Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    logger.info("Shutting down: Closing database engine...")
    await engine.dispose()

app = FastAPI(
    title="T2 Logistics API",
    version="1.0.0",
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
api_v1_router.include_router(insights_router)
api_v1_router.include_router(routes_router)

app.include_router(benchmark_router)
app.include_router(api_v1_router)


@app.get(
    "/health",
    tags=["System"],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "System is healthy",
            "content": {
                "application/json": {
                    "example": {"status": "ok",
                                "database": "connected",
                                "models": {"qwen": "loaded",
                                           "llama": "loaded"}},
                },
            },
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Database connection failed",
            "content": {
                "application/json": {
                    "example": {"detail": "Database disconnected"},
                },
            },
        },
    },
)
async def health_check(session: AsyncSession = Depends(get_session)):
    """
    Health check endpoint that verifies database connectivity.
    """
    try:
        await session.execute(text("SELECT 1"))
        from src.models.qwen_client import QwenClient
        from src.models.llama_client import LlamaClient
        qwen_loaded = QwenClient._llm is not None
        llama_loaded = LlamaClient._llm is not None
        return {
            "status": "ok",
            "database": "connected",
            "models": {
                "qwen": "loaded" if qwen_loaded else "not_loaded",
                "llama": "loaded" if llama_loaded else "not_loaded",
            },
        }
    except Exception as exc:
        logger.error(f"Health check failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database disconnected",
        )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
