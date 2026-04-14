from typing import Type
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import (
    Location,
    SalesRep,
    VisitSchedule,
    DailyRouteOverride,
    VisitLog,
    ForceMajeureEvent,
    SkippedVisitStash,
    Route,
    Metric,
    OptimizationResult,
    Holiday,
    AuditLog,
    Vehicle,
    get_session,
)

# ==========================================
# ALL CRUD ROUTERS WILL BE GROUPED IN SWAGGER
# UNDER ONE TAG: "Tables"
# ==========================================
CRUD_TAG = "Tables"


def create_crud_router(model: Type, prefix: str) -> APIRouter:
    """
    Универсальный CRUD generator для всех таблиц.
    Все CRUD endpoints попадают в Swagger tag = Tables
    """

    router = APIRouter(tags=[CRUD_TAG])

    # =========================
    # CREATE
    # =========================
    @router.post(f"/{prefix}")
    async def create_item(
        payload: dict,
        db: AsyncSession = Depends(get_session),
    ):
        obj = model(**payload)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)

        return {
            "message": f"{model.__name__} created successfully",
            "data": {
                key: value
                for key, value in obj.__dict__.items()
                if not key.startswith("_")
            },
        }

    # =========================
    # READ ALL
    # =========================
    @router.get(f"/{prefix}")
    async def get_all_items(
        limit: int = Query(100),
        db: AsyncSession = Depends(get_session),
    ):
        stmt = select(model).limit(limit)
        result = await db.execute(stmt)
        items = result.scalars().all()

        return {
            prefix: [
                {
                    key: value
                    for key, value in item.__dict__.items()
                    if not key.startswith("_")
                }
                for item in items
            ]
        }

    # =========================
    # READ ONE
    # =========================
    @router.get(f"/{prefix}" + "/{item_id}")
    async def get_item(
        item_id: str,
        db: AsyncSession = Depends(get_session),
    ):
        stmt = select(model).where(model.id == item_id)
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()

        if not item:
            raise HTTPException(
                status_code=404,
                detail=f"{model.__name__} not found",
            )

        return {
            "data": {
                key: value
                for key, value in item.__dict__.items()
                if not key.startswith("_")
            }
        }

    # =========================
    # UPDATE
    # =========================
    @router.put(f"/{prefix}" + "/{item_id}")
    async def update_item(
        item_id: str,
        payload: dict,
        db: AsyncSession = Depends(get_session),
    ):
        stmt = select(model).where(model.id == item_id)
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()

        if not item:
            raise HTTPException(
                status_code=404,
                detail=f"{model.__name__} not found",
            )

        for key, value in payload.items():
            setattr(item, key, value)

        await db.commit()
        await db.refresh(item)

        return {
            "message": f"{model.__name__} updated successfully",
            "data": {
                key: value
                for key, value in item.__dict__.items()
                if not key.startswith("_")
            },
        }

    # =========================
    # DELETE
    # =========================
    @router.delete(f"/{prefix}" + "/{item_id}")
    async def delete_item(
        item_id: str,
        db: AsyncSession = Depends(get_session),
    ):
        stmt = select(model).where(model.id == item_id)
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()

        if not item:
            raise HTTPException(
                status_code=404,
                detail=f"{model.__name__} not found",
            )

        await db.delete(item)
        await db.commit()

        return {
            "message": f"{model.__name__} deleted successfully",
            "id": item_id,
        }

    return router


# =====================================================
# CRUD ROUTERS
# ALL WILL APPEAR UNDER "Tables"
# =====================================================

location_router_crud = create_crud_router(Location, "locations")
sales_rep_router_crud = create_crud_router(SalesRep, "sales-reps")
visit_schedule_router_crud = create_crud_router(VisitSchedule, "visit-schedule")
daily_route_router_crud = create_crud_router(DailyRouteOverride, "daily-route-overrides")
visit_log_router_crud = create_crud_router(VisitLog, "visit-log")
force_majeure_router_crud = create_crud_router(ForceMajeureEvent, "force-majeure-events")
skipped_visit_router_crud = create_crud_router(SkippedVisitStash, "skipped-visit-stash")
route_router_crud = create_crud_router(Route, "routes")
metric_router_crud = create_crud_router(Metric, "metrics")
optimization_router_crud = create_crud_router(OptimizationResult, "optimization-results")
audit_log_router_crud = create_crud_router(AuditLog, "audit-log")
vehicle_router_crud = create_crud_router(Vehicle, "vehicles")


# =====================================================
# HOLIDAY SPECIAL CASE (PK = date)
# =====================================================

holiday_router_crud = APIRouter(tags=[CRUD_TAG])


@holiday_router_crud.post("/holidays")
async def create_holiday(
    payload: dict,
    db: AsyncSession = Depends(get_session),
):
    obj = Holiday(**payload)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)

    return {
        "message": "Holiday created successfully",
        "data": {
            "date": obj.date,
            "name": obj.name,
            "is_working": obj.is_working,
        },
    }


@holiday_router_crud.get("/holidays")
async def get_holidays(
    db: AsyncSession = Depends(get_session),
):
    stmt = select(Holiday)
    result = await db.execute(stmt)
    holidays = result.scalars().all()

    return {
        "holidays": [
            {
                "date": h.date,
                "name": h.name,
                "is_working": h.is_working,
            }
            for h in holidays
        ]
    }