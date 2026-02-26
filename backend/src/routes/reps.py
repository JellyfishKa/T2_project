from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import SalesRep, get_session
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
    return rep


@router.delete("/{rep_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rep(
    rep_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Удалить сотрудника."""
    rep = await session.get(SalesRep, rep_id)
    if not rep:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")
    await session.delete(rep)
    await session.commit()
