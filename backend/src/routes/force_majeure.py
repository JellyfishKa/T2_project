from calendar import monthrange
from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import ForceMajeureEvent, get_session
from src.schemas.force_majeure import ForceMajeureRequest, ForceMajeureResponse, RedistributedItem
from src.services.force_majeure_service import ForceMajeureService

router = APIRouter(prefix="/force_majeure", tags=["Force Majeure"])


@router.post("/", response_model=ForceMajeureResponse, status_code=201)
async def create_force_majeure(
    req: ForceMajeureRequest,
    session: AsyncSession = Depends(get_session),
):
    """Зафиксировать форс-мажор и выполнить авторедистрибуцию ТТ."""
    service = ForceMajeureService(session)
    try:
        result = await service.handle(
            rep_id=req.rep_id,
            event_date=req.event_date,
            fm_type=req.type,
            description=req.description,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return _dict_to_response(result)


@router.get("/", response_model=List[ForceMajeureResponse])
async def list_force_majeure(
    month: str = Query(..., description="Месяц YYYY-MM"),
    session: AsyncSession = Depends(get_session),
):
    """История форс-мажоров за месяц."""
    try:
        year, m = map(int, month.split("-"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат месяца. Используй YYYY-MM")

    _, last_day = monthrange(year, m)
    stmt = (
        select(ForceMajeureEvent)
        .where(
            ForceMajeureEvent.event_date >= date(year, m, 1),
            ForceMajeureEvent.event_date <= date(year, m, last_day),
        )
        .options(selectinload(ForceMajeureEvent.rep))
        .order_by(ForceMajeureEvent.event_date)
    )
    result = await session.execute(stmt)
    events = result.scalars().all()

    return [
        _event_to_response(e)
        for e in events
    ]


# ---------------------------------------------------------------------------

def _dict_to_response(d: dict) -> ForceMajeureResponse:
    from datetime import datetime
    redist = [
        RedistributedItem(
            rep_id=r["rep_id"],
            rep_name=r["rep_name"],
            location_ids=r["location_ids"],
            new_date=date.fromisoformat(r["new_date"]),
        )
        for r in d.get("redistributed_to", [])
    ]
    return ForceMajeureResponse(
        id=d["id"],
        type=d["type"],
        rep_id=d["rep_id"],
        rep_name=d["rep_name"],
        event_date=date.fromisoformat(d["event_date"]),
        description=d.get("description"),
        affected_tt_count=d["affected_tt_count"],
        redistributed_to=redist,
        created_at=datetime.fromisoformat(d["created_at"]) if d.get("created_at") else datetime.now(),
    )


def _event_to_response(e: ForceMajeureEvent) -> ForceMajeureResponse:
    rep_name = e.rep.name if e.rep else e.rep_id
    redist_raw = e.redistributed_to or []
    redist = [
        RedistributedItem(
            rep_id=r["rep_id"],
            rep_name=r.get("rep_name", r["rep_id"]),
            location_ids=r.get("location_ids", []),
            new_date=date.fromisoformat(r["new_date"]) if isinstance(r.get("new_date"), str) else r["new_date"],
        )
        for r in redist_raw
    ]
    return ForceMajeureResponse(
        id=e.id,
        type=e.type,
        rep_id=e.rep_id,
        rep_name=rep_name,
        event_date=e.event_date,
        description=e.description,
        affected_tt_count=len(e.affected_tt_ids or []),
        redistributed_to=redist,
        created_at=e.created_at,
    )
