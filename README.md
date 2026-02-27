# T2 Розничная сеть

**AI-powered оптимизация маршрутов, управление расписанием и сетевая аналитика для торговых представителей**

## Описание проекта

T2 — комплексная платформа на основе искусственного интеллекта для управления посещениями торговых точек (ТТ) Мордовии. Система автоматически строит месячное расписание с учётом категорий ТТ (A/B/C/D), оптимизирует маршруты через LLM, трекает фактическое время на каждой ТТ и выгружает полную аналитику в Excel.

**Длительность разработки**: 4 недели
**Размер команды**: 3 разработчика + 1 TL/PM
**Методология**: Agile Lite (Kanban)
**Статус**: ✅ Production-Ready

---

## Цели проекта

### Неделя 1-2: Инфраструктура + LLM интеграция ✅
- [x] Интегрированы 2 LLM-модели (Qwen 0.5B, Llama 3.2 1B)
- [x] Оптимизация маршрутов работает (`POST /optimize`)
- [x] Панель управления и аналитика готовы
- [x] Тестовое покрытие > 60%

### Неделя 3: Production-Ready ✅
- [x] Fallback-механизм (Qwen → Llama → Greedy)
- [x] Docker + CI/CD настроен
- [x] Удалена T-Pro, система стабилизирована

### Неделя 4: Управление расписанием и аналитика ✅
- [x] Алгоритм планировщика расписания (категории A/B/C/D)
- [x] Трекинг времени на каждой ТТ (`time_in`/`time_out`)
- [x] Детальный просмотр дня + LLM-варианты маршрута
- [x] Форс-мажоры с автоперераспределением визитов
- [x] Excel экспорт (4 листа) + Excel импорт с результатами
- [x] Реальная аналитика (охват ТТ, активность ТП, инсайты)

---

## Архитектура

### Технологический стек

**Backend**:
- Python 3.11+ / FastAPI (async REST API)
- SQLAlchemy async + Alembic (ORM + миграции)
- PostgreSQL (основная БД)
- Qwen2-0.5B + Llama-3.2-1B (GGUF через llama-cpp-python)
- openpyxl (Excel экспорт/импорт)

**Frontend**:
- Vue 3 + Vite + TypeScript
- TailwindCSS
- Chart.js + vue-chartjs (графики)
- Axios (HTTP-клиент)

**DevOps**:
- Docker + Docker Compose
- GitHub Actions (CI/CD)
- Nginx (reverse proxy)

---

## Структура репозитория

```
T2_project/
├── README.md
├── PLAN.md                          # Требования конкурса
├── .env.example
├── docker-compose.yml
│
├── docs/
│   ├── AGILE_LITE_QUICKSTART.md
│   ├── EXECUTIVE_SUMMARY.md         # Исполнительное резюме
│   ├── TEAM_PLAYBOOK.md
│   ├── API_CONTRACT.md              # Спецификация всех эндпоинтов
│   ├── ARCHITECTURE.md              # Дизайн системы
│   ├── PLANS/
│   │   ├── TEST_PLAN_WEEK1.md
│   │   ├── TEST_PLAN_WEEK2.md
│   │   ├── TEST_PLAN_WEEK3.md
│   │   └── TEST_PLAN_WEEK4.md      # ← НОВЫЙ: тест-план недели 4
│   ├── WEEK_TASKS/
│   │   ├── WEEK_1_PLAN.md
│   │   ├── WEEK_2_PLAN.md
│   │   ├── WEEK_3_PLAN.md
│   │   └── WEEK_4_PLAN.md          # ← НОВЫЙ: таски недели 4
│   ├── MVP/
│   │   ├── MVP_RELEASE_NOTES.md
│   │   ├── MVP_DEMO_CHECKLIST.md
│   │   └── MVP_STAKEHOLDER_SUMMARY.md
│   └── SERVER/
│       ├── DEPLOYMENT_GUIDE.md
│       └── MODEL_SETUP_GUIDE.md
│
├── backend/
│   ├── main.py                      # FastAPI приложение
│   ├── src/
│   │   ├── database/
│   │   │   ├── models.py            # ORM: Location, Route, SalesRep, VisitSchedule, VisitLog, ...
│   │   │   └── migrations/
│   │   ├── models/
│   │   │   ├── qwen_client.py       # Qwen2-0.5B
│   │   │   └── llama_client.py      # Llama-3.2-1B
│   │   ├── routes/
│   │   │   ├── optimize.py          # POST /optimize, /optimize/variants, /optimize/confirm
│   │   │   ├── schedule.py          # GET/POST /schedule
│   │   │   ├── reps.py              # CRUD /reps
│   │   │   ├── force_majeure.py     # POST /force_majeure
│   │   │   ├── visits.py            # GET/POST /visits
│   │   │   ├── export.py            # GET /export/schedule (Excel)
│   │   │   ├── import_excel.py      # POST /import/schedule (Excel)
│   │   │   ├── insights.py          # GET /insights
│   │   │   ├── metrics.py           # GET /metrics
│   │   │   └── locations.py         # CRUD /locations
│   │   ├── schemas/                 # Pydantic схемы
│   │   └── services/
│   │       ├── optimize.py          # Optimizer + generate_variants()
│   │       ├── schedule_planner.py  # SchedulePlanner (алгоритм планирования)
│   │       └── force_majeure_service.py
│   └── tests/
│
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   ├── AnalyticsView.vue    # Аналитика + Excel импорт/экспорт
│   │   │   ├── ScheduleView.vue     # Расписание + Day modal + LLM варианты
│   │   │   ├── RepsView.vue         # Управление сотрудниками
│   │   │   ├── OptimizeView.vue     # Форма оптимизации маршрута
│   │   │   └── DashboardView.vue    # Главная панель
│   │   ├── services/
│   │   │   ├── api.ts               # Все API-вызовы
│   │   │   └── types.ts             # TypeScript типы
│   │   └── tests/
│       │   └── views/
│       │       ├── AnalyticsView.spec.ts
│       │       └── OptimizeView.spec.ts
│
├── scripts/
│   └── generate_mordovia_dataset.py # Генератор 250 ТТ Мордовии
│
├── data/
│   └── locations_mordovia_250.json  # 250 ТТ с координатами
│
└── ml/
    └── benchmarks/
```

---

## Быстрый старт

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

---

## Ключевые функции

### 1. Оптимизация маршрутов (LLM)
- Единый endpoint `POST /optimize` с авто-fallback (Qwen → Llama → Greedy)
- **3 варианта маршрута** с pros/cons от LLM (`POST /optimize/variants`)
- Сохранение выбранного варианта (`POST /optimize/confirm`)

### 2. Расписание визитов
- Автоматическая генерация месячного плана с учётом категорий ТТ:
  - **A**: 3 визита/мес (критические)
  - **B**: 2 визита/мес
  - **C**: 1 визит/мес
  - **D**: 1 визит/квартал
- Ограничение: max 14 ТТ на ТП в день (рабочий день 09:00–18:00)

### 3. Трекинг времени на ТТ
- Фиксация `time_in` и `time_out` при отметке визита выполненным
- Автоматический расчёт длительности в UI (`(22м)`)
- Хранение в `VisitLog`, доступ через API и Excel

### 4. Форс-мажоры
- Регистрация болезни/отпуска сотрудника
- Автоматическое перераспределение его визитов на свободных ТП

### 5. Excel интеграция
```
Экспорт: GET /api/v1/export/schedule?month=YYYY-MM
  → t2_schedule_YYYY-MM.xlsx с 4 листами:
    • Расписание     — все плановые визиты
    • Журнал визитов — фактические визиты с длительностью
    • Статистика по ТТ — охват, % выполнения по категориям
    • Активность ТП  — выходы на маршрут, % выполнения

Импорт: POST /api/v1/import/schedule (multipart/form-data)
  → Загрузка заполненного Excel → обновление статусов + VisitLog
  → Возвращает {updated, skipped, errors}
```

### 6. Аналитика и инсайты
- Охват ТТ (`coverage_percent`) за месяц
- Статистика по категориям A/B/C/D
- Активность торговых представителей (выходы на маршрут)
- Сравнение моделей (время ответа, качество, стоимость)

---

## API Endpoints

### Оптимизация маршрутов
| Метод | Endpoint | Назначение |
|-------|----------|-----------|
| POST | `/api/v1/optimize` | Оптимизация (авто-fallback) |
| POST | `/api/v1/optimize/variants` | 3 варианта с LLM pros/cons |
| POST | `/api/v1/optimize/confirm` | Сохранить выбранный вариант |
| POST | `/api/v1/qwen/optimize` | Прямой вызов Qwen |
| POST | `/api/v1/llama/optimize` | Прямой вызов Llama |

### Расписание и визиты
| Метод | Endpoint | Назначение |
|-------|----------|-----------|
| POST | `/api/v1/schedule/generate` | Генерация месячного плана |
| GET  | `/api/v1/schedule/` | Список визитов (фильтры) |
| PATCH| `/api/v1/schedule/{id}/status` | Обновить статус + время |
| GET  | `/api/v1/visits` | История фактических визитов |
| POST | `/api/v1/force_majeure` | Регистрация форс-мажора |

### Локации и сотрудники
| Метод | Endpoint | Назначение |
|-------|----------|-----------|
| GET  | `/api/v1/locations/` | Список ТТ |
| POST | `/api/v1/locations/` | Создание ТТ |
| GET  | `/api/v1/reps` | Список ТП |
| POST | `/api/v1/reps` | Создание ТП |
| PATCH| `/api/v1/reps/{id}` | Обновление ТП |

### Аналитика и отчётность
| Метод | Endpoint | Назначение |
|-------|----------|-----------|
| GET  | `/api/v1/metrics` | Метрики моделей |
| GET  | `/api/v1/insights?month=YYYY-MM` | Инсайты по охвату ТТ |
| GET  | `/api/v1/export/schedule?month=YYYY-MM` | Скачать Excel (4 листа) |
| POST | `/api/v1/import/schedule` | Загрузить заполненный Excel |
| GET  | `/api/v1/routes/` | Список маршрутов |
| GET  | `/health` | Health check |

---

## Тестирование

```bash
# Frontend (182 тестов)
cd frontend && npx vitest run

# Backend (61 тест)
cd backend && pytest tests/ -v

# TypeScript проверка
cd frontend && npx vue-tsc --noEmit

# ML бенчмарки
python ml/benchmarks/llm_benchmark.py --mock
```

### Покрытие тестами

| Компонент | Тестов | Coverage |
|-----------|--------|----------|
| Backend | 61 | 64% |
| Frontend | 182 | ~70% |
| ML | 15 | ~80% |

---

## Статус проекта

| Фаза | Функционал | Статус |
|------|-----------|--------|
| Оптимизация маршрутов | Qwen + Llama + Greedy fallback | ✅ |
| Расписание визитов | Алгоритм A/B/C/D, 14 ТТ/день | ✅ |
| Трекинг времени | time_in/time_out → длительность | ✅ |
| Форс-мажоры | Регистрация + перераспределение | ✅ |
| Excel экспорт | 4 листа с форматированием | ✅ |
| Excel импорт | Обновление статусов + VisitLog | ✅ |
| LLM варианты | 3 варианта + pros/cons | ✅ |
| Аналитика | Охват, активность, инсайты | ✅ |
| Docker deployment | docker-compose up -d | ✅ |
| CI/CD | GitHub Actions, 182+61 тестов | ✅ |

---

## Переменные окружения

```env
# LLM Models
QWEN_MODEL_ID=qwen2-0_5b-instruct-q4_k_m.gguf
LLAMA_MODEL_ID=Llama-3.2-1B-Instruct-Q4_K_M.gguf

# Database
DATABASE_USER=postgres
DATABASE_PASSWORD=your_secure_password
DATABASE_HOST=localhost
DATABASE_NAME=t2
DATABASE_PORT=5432

# CORS (для продакшена)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## Ресурсы моделей

| Модель | Файл | RAM | Диск |
|--------|------|-----|------|
| Qwen2-0.5B-Instruct | qwen2-0_5b-instruct-q4_k_m.gguf | ~0.6 GB | ~400 MB |
| Llama-3.2-1B-Instruct | Llama-3.2-1B-Instruct-Q4_K_M.gguf | ~1.2 GB | ~808 MB |
| **Итого** | | **~1.8 GB** | **~1.2 GB** |

---

## Документация

| Документ | Назначение |
|----------|-----------|
| [WEEK_4_PLAN.md](docs/WEEK_TASKS/WEEK_4_PLAN.md) | Таски и исполнители — неделя 4 |
| [TEST_PLAN_WEEK4.md](docs/PLANS/TEST_PLAN_WEEK4.md) | Тест-кейсы — неделя 4 |
| [API_CONTRACT.md](docs/API_CONTRACT.md) | Полная спецификация API |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Архитектура системы |
| [DEPLOYMENT_GUIDE.md](docs/SERVER/DEPLOYMENT_GUIDE.md) | Деплой на сервер |
| [MVP_RELEASE_NOTES.md](docs/MVP/MVP_RELEASE_NOTES.md) | История релизов |

---

## Команда

| Роль | Имя | Ответственность |
|------|-----|----------------|
| Backend | Роман Кижаев | API, БД, LLM клиенты, Excel |
| Frontend | Владислав Наумкин | Vue, TypeScript, UI/UX |
| ML/Analytics | Дмитрий Мукасеев | Алгоритмы, датасет, инсайты |
| TL/PM | Сергей Маклаков | Архитектура, CI, документация |

---

*Последнее обновление: 27 февраля 2026*
