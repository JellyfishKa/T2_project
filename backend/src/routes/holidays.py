"""
Управление праздничными днями.

GET  /holidays?month=YYYY-MM  — праздники за месяц
GET  /holidays?year=YYYY      — праздники за год
PATCH /holidays/{date}        — изменить статус (рабочий/нерабочий)
"""
from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Holiday, VisitSchedule, get_session

router = APIRouter(prefix="/holidays", tags=["Holidays"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class HolidayResponse(BaseModel):
    date: date_type
    name: str
    is_working: bool

    class Config:
        from_attributes = True


class HolidayPatchRequest(BaseModel):
    is_working: bool


class HolidayPatchResponse(BaseModel):
    date: date_type
    name: str
    is_working: bool
    affected_visits_count: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[HolidayResponse])
async def list_holidays(
    month: str | None = Query(None, description="YYYY-MM"),
    year: int | None = Query(None, description="YYYY"),
    session: AsyncSession = Depends(get_session),
):
    """Возвращает список праздников за месяц или за год."""
    stmt = select(Holiday).order_by(Holiday.date)

    if month:
        try:
            y, m = map(int, month.split("-"))
        except ValueError:
            raise HTTPException(status_code=422, detail="month должен быть в формате YYYY-MM")
        from calendar import monthrange
        _, last_day = monthrange(y, m)
        stmt = stmt.where(
            Holiday.date >= date_type(y, m, 1),
            Holiday.date <= date_type(y, m, last_day),
        )
    elif year:
        stmt = stmt.where(
            Holiday.date >= date_type(year, 1, 1),
            Holiday.date <= date_type(year, 12, 31),
        )

    result = await session.execute(stmt)
    return result.scalars().all()


@router.patch("/{holiday_date}", response_model=HolidayPatchResponse)
async def patch_holiday(
    holiday_date: str,
    body: HolidayPatchRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Изменяет статус праздничного дня (рабочий / нерабочий).
    Возвращает количество уже запланированных визитов на этот день
    (актуально при переводе в нерабочий — их нужно перенести).
    """
    try:
        d = date_type.fromisoformat(holiday_date)
    except ValueError:
        raise HTTPException(status_code=422, detail="Дата должна быть в формате YYYY-MM-DD")

    holiday = await session.get(Holiday, d)
    if not holiday:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Праздник {holiday_date} не найден в базе",
        )

    holiday.is_working = body.is_working
    await session.commit()
    await session.refresh(holiday)

    # Считаем запланированные визиты на этот день
    count_result = await session.execute(
        select(func.count()).where(
            VisitSchedule.planned_date == d,
            VisitSchedule.status.in_(["planned", "rescheduled"]),
        )
    )
    affected = count_result.scalar() or 0

    return HolidayPatchResponse(
        date=holiday.date,
        name=holiday.name,
        is_working=holiday.is_working,
        affected_visits_count=affected,
    )
