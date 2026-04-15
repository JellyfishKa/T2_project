from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import SalesRep, VisitSchedule, get_session
from src.schemas.reps import SalesRepCreate, SalesRepResponse, SalesRepUpdate

router = APIRouter(prefix="/reps", tags=["Sales Reps"])


@router.get("/", response_model=List[SalesRepResponse])
async def get_reps(session: AsyncSession = Depends(get_session)):
    """Список всех сотрудников."""
    result = await session.execute(select(SalesRep).order_by(SalesRep.name))
    return result.scalars().all()


@router.post("/", response_model=SalesRepResponse, status_code=status.HTTP_201_CREATED)
async def create_rep(
    data: SalesRepCreate,
    session: AsyncSession = Depends(get_session),
):
    """Создать нового торгового представителя."""
    rep = SalesRep(name=data.name, status=data.status)
    session.add(rep)
    await session.commit()
    await session.refresh(rep)
    return rep


@router.patch("/{rep_id}", response_model=SalesRepResponse)
async def update_rep(
    rep_id: str,
    data: SalesRepUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Обновить имя или статус сотрудника."""
    rep = await session.get(SalesRep, rep_id)
    if not rep:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")
    if data.name is not None:
        rep.name = data.name
    if data.status is not None:
        rep.status = data.status
    await session.commit()
    await session.refresh(rep)

    # Warning: если новый статус sick/vacation — считаем будущие planned-визиты
    warning: str | None = None
    pending_count = 0
    if data.status in ("sick", "vacation"):
        today = date.today()
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

    result = SalesRepResponse(
        id=rep.id,
        name=rep.name,
        status=rep.status,
        created_at=rep.created_at,
        warning=warning,
        pending_visits_count=pending_count,
    )
    return result


@router.delete("/{rep_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rep(
    rep_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Удалить сотрудника."""
    rep = await session.get(SalesRep, rep_id)
    if not rep:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")
    session.delete(rep)
    await session.commit()
