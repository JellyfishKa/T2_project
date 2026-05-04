from datetime import datetime
from typing import List, Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models import (
    DailyRouteOverride,
    ForceMajeureEvent,
    SalesRep,
    SkippedVisitStash,
    VisitLog,
    VisitSchedule,
    get_session,
)
from src.schemas.reps import SalesRepCreate, SalesRepResponse, SalesRepUpdate

router = APIRouter(prefix="/reps", tags=["Sales Reps"])


def _to_response(rep: SalesRep, warning: Optional[str] = None, pending_count: int = 0) -> SalesRepResponse:
    return SalesRepResponse(
        id=rep.id,
        name=rep.name,
        status=rep.status,
        vehicle_id=rep.vehicle_id,
        vehicle_name=rep.vehicle.name if rep.vehicle else None,
        created_at=rep.created_at,
        warning=warning,
        pending_visits_count=pending_count,
    )


@router.get("/", response_model=List[SalesRepResponse])
async def get_reps(session: AsyncSession = Depends(get_session)):
    """Список всех сотрудников."""
    result = await session.execute(
        select(SalesRep).options(selectinload(SalesRep.vehicle)).order_by(SalesRep.name)
    )
    return [_to_response(r) for r in result.scalars().all()]


@router.post("/", response_model=SalesRepResponse, status_code=status.HTTP_201_CREATED)
async def create_rep(
    data: SalesRepCreate,
    session: AsyncSession = Depends(get_session),
):
    """Создать нового торгового представителя."""
    rep = SalesRep(name=data.name, status=data.status, vehicle_id=getattr(data, "vehicle_id", None))
    session.add(rep)
    await session.commit()
    await session.execute(
        select(SalesRep).options(selectinload(SalesRep.vehicle)).where(SalesRep.id == rep.id)
    )
    await session.refresh(rep)
    # Re-fetch with vehicle loaded
    result = await session.execute(
        select(SalesRep).options(selectinload(SalesRep.vehicle)).where(SalesRep.id == rep.id)
    )
    rep = result.scalar_one()
    return _to_response(rep)


@router.patch("/{rep_id}", response_model=SalesRepResponse)
async def update_rep(
    rep_id: str,
    data: SalesRepUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Обновить имя, статус или привязанный автомобиль сотрудника."""
    result = await session.execute(
        select(SalesRep).options(selectinload(SalesRep.vehicle)).where(SalesRep.id == rep_id)
    )
    rep = result.scalar_one_or_none()
    if not rep:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")

    if data.name is not None:
        rep.name = data.name
    if data.status is not None:
        rep.status = data.status
    if "vehicle_id" in data.model_fields_set:
        rep.vehicle_id = data.vehicle_id

    await session.commit()

    # Re-fetch with vehicle loaded after commit
    result = await session.execute(
        select(SalesRep).options(selectinload(SalesRep.vehicle)).where(SalesRep.id == rep_id)
    )
    rep = result.scalar_one()

    # Warning: если новый статус sick/vacation — считаем будущие planned-визиты
    warning: str | None = None
    pending_count = 0
    if data.status in ("sick", "vacation"):
        today = datetime.now(ZoneInfo("Europe/Moscow")).date()
        cnt_result = await session.execute(
            select(func.count()).where(
                VisitSchedule.rep_id == rep_id,
                VisitSchedule.planned_date >= today,
                VisitSchedule.status == "planned",
            )
        )
        pending_count = cnt_result.scalar() or 0
        if pending_count > 0:
            status_label = "на больничном" if data.status == "sick" else "в отпуске"
            warning = (
                f"Сотрудник переведён {status_label}. "
                f"Есть {pending_count} незакрытых плановых визитов — "
                f"рекомендуется создать форс-мажор для перераспределения."
            )

    return _to_response(rep, warning, pending_count)


@router.delete("/{rep_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rep(
    rep_id: str,
    force: bool = Query(False, description="Если true — удалить сотрудника вместе со связанными тестовыми данными"),
    session: AsyncSession = Depends(get_session),
):
    """Удалить сотрудника."""
    rep = await session.get(SalesRep, rep_id)
    if not rep:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")

    schedules_count = (
        await session.execute(
            select(func.count()).where(VisitSchedule.rep_id == rep_id)
        )
    ).scalar() or 0
    visits_count = (
        await session.execute(
            select(func.count()).where(VisitLog.rep_id == rep_id)
        )
    ).scalar() or 0
    fm_count = (
        await session.execute(
            select(func.count()).where(ForceMajeureEvent.rep_id == rep_id)
        )
    ).scalar() or 0
    overrides_count = (
        await session.execute(
            select(func.count()).where(DailyRouteOverride.rep_id == rep_id)
        )
    ).scalar() or 0
    stash_count = (
        await session.execute(
            select(func.count()).where(SkippedVisitStash.rep_id == rep_id)
        )
    ).scalar() or 0

    protected_records = (
        schedules_count + visits_count + fm_count + overrides_count + stash_count
    )
    if force:
        await session.execute(delete(VisitLog).where(VisitLog.rep_id == rep_id))
        await session.execute(delete(DailyRouteOverride).where(DailyRouteOverride.rep_id == rep_id))
        await session.execute(delete(ForceMajeureEvent).where(ForceMajeureEvent.rep_id == rep_id))
        await session.execute(delete(SkippedVisitStash).where(SkippedVisitStash.rep_id == rep_id))
        await session.execute(delete(VisitSchedule).where(VisitSchedule.rep_id == rep_id))
        await session.delete(rep)
        await session.commit()
        return

    if protected_records > 0:
        raise HTTPException(
            status_code=409,
            detail=(
                "Сотрудника нельзя удалить: у него есть связанные расписания, "
                "визиты или история форс-мажоров. Сначала переведите его в "
                "неактивный статус."
            ),
        )

    await session.delete(rep)
    await session.commit()
