# CONTRIBUTING.md — Руководство для разработчика

> Последнее обновление: 29 апреля 2026



## Структура проекта

T2_project/
├── backend/                     
│   ├── src/
│   │   ├── database/           
│   │   │   ├── migrations/         
│   │   │   ├── models.py        
│   │   │   └── __init__.py
│   │   ├── routes/             
│   │   │   ├── optimize.py
│   │   │   ├── schedule.py
│   │   │   ├── holidays.py
│   │   │   ├── audit_log.py
│   │   │   └── ...
│   │   ├── services/           
│   │   │   ├── optimize.py      
│   │   │   ├── schedule_planner.py
│   │   │   ├── force_majeure_service.py
│   │   │   └── ...
│   │   ├── models/              
│   │   │   ├── llm_client.py    
│   │   │   ├── qwen_client.py   
│   │   │   ├── llama_client.py  
│   │   │   ├── geo_utils.py     
│   │   │   └── schemas.py       
│   │   ├── schemas/             
│   │   └──config.py           
│   ├── tests/    
│   ├── requirements/                   
│   ├── main.py
│   └── .env                    
│
├── frontend/                    
│   ├── src/
│   │   ├── views/              
│   │   ├── components/          
│   │   ├── services/
│   │   │   ├── types.ts        
│   │   │   └── api.ts
│   │   └── tests/               
│   └── package.json
│
├── ml/                          
│   ├── benchmarks/
│   │   └── llm_benchmark.py
│   ├── tests/
│   └── test_models.py           
│
├── docker-compose.yml
├── .env.example
└── docs/



## Локальный запуск

### Требования
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

### Настройка Backend

```bash
git clone https://github.com/JellyfishKa/T2_project.git
cd T2_project

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r backend/requirements/prod/requirements.txt

cp .env.example .env
# Отредактируй .env (DATABASE_*, GGUF-модели)

cd backend
python -m uvicorn main:app --reload
```

Backend: `http://localhost:8000`
Swagger UI: `http://localhost:8000/docs`

### Настройка Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`

### Docker (все сервисы)

```bash
cp .env.example .env
docker-compose up -d
curl http://localhost:8000/health
```



## Добавление нового роута

### 1. Создать файл роута

```bash
touch backend/src/routes/my_feature.py
```

### 2. Написать роут

# backend/src/routes/my_feature.py
```bash
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database.models import get_session, MyModel
from src.schemas.my_feature import MyRequest, MyResponse

router = APIRouter(prefix="/my-feature", tags=["My Feature"])


@router.get("/", response_model=list[MyResponse])
async def get_all(
    session: AsyncSession = Depends(get_session),
):
    """Получить все записи."""
    result = await session.execute(select(MyModel))
    return result.scalars().all()


@router.get("/{item_id}", response_model=MyResponse)
async def get_one(
    item_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Получить запись по ID."""
    item = await session.get(MyModel, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item


@router.post("/", response_model=MyResponse, status_code=201)
async def create(
    data: MyRequest,
    session: AsyncSession = Depends(get_session),
):
    """Создать новую запись."""
    item = MyModel(**data.model_dump())
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


@router.patch("/{item_id}", response_model=MyResponse)
async def update(
    item_id: str,
    data: MyRequest,
    session: AsyncSession = Depends(get_session),
):
    """Обновить запись."""
    item = await session.get(MyModel, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    await session.commit()
    await session.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
async def delete(
    item_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Удалить запись."""
    item = await session.get(MyModel, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    await session.delete(item)
    await session.commit()
```

### 3. Зарегистрировать роут в main.py

# backend/src/main.py
```bash
from src.routes import my_feature

app.include_router(my_feature.router)
```

### 4. Добавить Pydantic схему

# backend/src/schemas/my_feature.py
```bash
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class MyRequest(BaseModel):
    name: str
    value: float


class MyResponse(BaseModel):
    id: str
    name: str
    value: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
```
### 5. Добавить SQLAlchemy модель

# backend/src/database/models.py
```bash
class MyModel(Base):
    __tablename__ = "my_table"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

## Добавление нового сервиса

### 1. Создать файл сервиса
```bash
touch backend/src/services/my_service.py
```
### 2. Написать сервис

# backend/src/services/my_service.py
```bash
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database.models import MyModel

logger = logging.getLogger("my_service")


class MyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process(self, data: dict) -> dict:
        """Основная бизнес-логика."""
        logger.info(f"Processing: {data}")
        # Валидация, расчёты, вызовы других сервисов
        result = {"processed": True, "data": data}
        return result

    async def get_by_id(self, item_id: str) -> Optional[MyModel]:
        """Получить запись."""
        return await self.db.get(MyModel, item_id)

    async def create(self, **kwargs) -> MyModel:
        """Создать запись."""
        item = MyModel(**kwargs)
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item
```
### 3. Использовать в роуте

# backend/src/routes/my_feature.py
```bash
from src.services.my_service import MyService

@router.post("/process")
async def process_data(
    data: MyRequest,
    session: AsyncSession = Depends(get_session),
):
    service = MyService(session)
    result = await service.process(data.model_dump())
    return result
```
### 4. Добавить логирование
```bash
Используйте стандартный логгер:

import logging
logger = logging.getLogger(__name__)
logger.info("Message")
logger.error("Error", exc_info=True)
```

## Создание миграции Alembic

### 1. Создать новую миграцию
```bash
cd backend

alembic revision -m "add_my_table"
```
### 2. Отредактировать миграцию

# backend/alembic/versions/008_add_my_table.py
```bash
"""008_add_my_table

Revision ID: 008_add_my_table
Revises: 007_route_comparison_snapshots
Create Date: 2026-04-29 12:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '008_add_my_table'
down_revision: Union[str, None] = '007_route_comparison_snapshots'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'my_table',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_my_table_id', 'my_table', ['id'])


def downgrade() -> None:
    op.drop_index('ix_my_table_id', table_name='my_table')
    op.drop_table('my_table')
```
### 3. Применить миграцию
```bash
alembic upgrade head
```
## Запуск тестов

```bash
cd frontend && npx vitest run

cd backend && pytest tests/ -v

cd frontend && npx vue-tsc --noEmit

cd e2e && npx playwright test tests/dashboard/route-comparison.spec.ts

python ml/benchmarks/llm_benchmark.py --mock
```