# АРХИТЕКТУРА И ТЕХНИЧЕСКИЙ ДИЗАЙН

> Последнее обновление: 27 февраля 2026 (Неделя 4)

---

## Обзор архитектуры

```
+-------------------------------------------------------+
|            Frontend (Vue 3 + TypeScript)              |
|  AnalyticsView | ScheduleView | OptimizeView | Reps   |
+------------------------+------------------------------+
                         |
                         v  HTTP/REST (/api/v1/...)
+-------------------------------------------------------+
|            Backend API (FastAPI + Python)             |
|  optimize | schedule | reps | force_majeure | visits  |
|  export   | import   | insights | metrics | locations |
+----------+----------------+-----------+---------------+
           |                |           |
           v                v           v
    +-----------+   +-----------+  +----------+
    |    LLM    |   | PostgreSQL|  |  openpyxl|
    |  Qwen 0.5B|   |   (ORM)   |  | (Excel)  |
    |  Llama 1B |   |           |  +----------+
    +-----------+   +-----------+
```

---

## Слой базы данных

### Таблицы

| Таблица | Назначение |
|---------|-----------|
| `locations` | Торговые точки (ТТ): координаты, категория A/B/C/D, адрес |
| `routes` | Оптимизированные маршруты (результаты LLM) |
| `metrics` | Метрики LLM-запросов (время, качество, стоимость) |
| `optimization_results` | История оптимизаций |
| `sales_reps` | Торговые представители (статус: active/sick/vacation/unavailable) |
| `visit_schedule` | Плановые визиты (FK → rep, location, дата, статус) |
| `visit_log` | Фактические визиты с `time_in`/`time_out` |
| `force_majeure_events` | Форс-мажоры с JSON перераспределения визитов |

### Связи

```
SalesRep ─────────────┐
                       │ (rep_id)
Location ──────────────┤
                       │
                  VisitSchedule ──── VisitLog
                       │              (schedule_id)
                       │
             ForceMajeureEvent
                  (rep_id -> redistributed_to JSON)
```

### Миграции Alembic

| Версия | Содержимое |
|--------|-----------|
| `001_initial_schema` | `locations`, `routes`, `metrics`, `optimization_results` |
| `002_add_reps_schedule` | `sales_reps`, `visit_schedule`, `visit_log`, `force_majeure_events`; расширение `locations`: category, city, district, address |

---

## Слой Backend

### Структура маршрутов (routes)

```
backend/src/routes/
  optimize.py          POST /optimize, /optimize/variants, /optimize/confirm
  schedule.py          POST /generate, GET /, PATCH /{id}/status, GET /daily
  reps.py              GET/POST/PATCH/DELETE /reps
  force_majeure.py     POST/GET /force_majeure
  visits.py            POST/GET /visits
  export.py            GET /export/schedule   (Excel 4 листа)
  import_excel.py      POST /import/schedule  (Excel -> БД)
  insights.py          GET /insights
  metrics.py           GET /metrics
  locations.py         GET/POST /locations
  routes.py            GET /routes
  qwen.py              POST /qwen/optimize
  llama.py             POST /llama/optimize
```

### Сервисный слой

```
backend/src/services/
  optimize.py              Optimizer.optimize() / generate_variants() / confirm_variant()
  schedule_planner.py      SchedulePlanner.generate_monthly_plan()
  force_majeure_service.py ForceMajeureService.redistribute()
```

### LLM-клиенты (Strategy Pattern)

```python
class LLMClient(ABC):
    @abstractmethod
    async def generate_route(locations: List[Location]) -> str: ...

class QwenClient(LLMClient):
    """Qwen2-0.5B-Instruct-Q4_K_M.gguf — основная модель"""

class LlamaClient(LLMClient):
    """Llama-3.2-1B-Instruct-Q4_K_M.gguf — fallback"""
```

### Fallback-цепочка оптимизации

```
POST /optimize
    |
    v
[Qwen] -- успех --> OptimizeResponse (model_used="qwen")
    |
  ошибка
    |
    v
[Llama] -- успех --> OptimizeResponse (model_used="llama", fallback_reason="...")
    |
  ошибка
    |
    v
[Greedy] -- всегда работает --> OptimizeResponse (model_used="greedy")
```

### Алгоритм SchedulePlanner

```
Входные данные: список ТТ (с категориями), список ТП, месяц

Определяем частоту визитов по категории:
  A -> 3/мес   B -> 2/мес   C -> 1/мес   D -> 1/квартал

Константы:
  WORK_MINUTES   = 540  (09:00-18:00)
  LUNCH_BREAK    = 30 мин
  VISIT_DURATION = 15 мин
  AVG_TRAVEL     = 20 мин
  MAX_TT_PER_DAY = floor((540-30) / 35) = 14

Итерируем по рабочим дням (Пн-Пт):
  Для каждого ТП: назначаем ТТ (приоритет A->B->C->D)
  Проверяем: count(ТП, день) <= MAX_TT_PER_DAY

Сохраняем VisitSchedule в БД
```

### Excel экспорт/импорт

```
Экспорт (export.py):
  openpyxl.Workbook() -> 4 листа -> BytesIO -> StreamingResponse

Импорт (import_excel.py):
  UploadFile -> openpyxl.load_workbook(data_only=True)
  -> iter_rows(min_row=3)
  -> матчинг по (planned_date, rep_name -> rep.id, loc_name -> loc.id)
  -> обновление VisitSchedule.status
  -> если completed + время -> создание/обновление VisitLog
  -> commit -> {updated, skipped, errors[:20]}
```

---

## Слой Frontend

### Страницы (Views)

| Файл | Маршрут | Назначение |
|------|---------|-----------|
| `DashboardView.vue` | `/` | Сводная статистика |
| `OptimizeView.vue` | `/optimize` | Форма оптимизации маршрута |
| `AnalyticsView.vue` | `/analytics` | Аналитика + Excel импорт/экспорт |
| `ScheduleView.vue` | `/schedule` | Месячный календарь + Day modal |
| `RepsView.vue` | `/reps` | CRUD торговых представителей |

### Сервисный слой (api.ts)

```typescript
// Оптимизация
optimize(locationIds, model)
optimizeVariants(locationIds, model, opts)
confirmVariant(payload)

// Расписание
fetchMonthlyPlan(month, repId?)
updateVisitStatus(id, status, timeIn?, timeOut?)

// Сотрудники
fetchReps(), createRep(data), updateRep(id, data), deleteRep(id)

// Excel
downloadScheduleExcel(month)
importScheduleExcel(file)

// Аналитика
fetchRoutes(offset, limit), getMetrics()
compareModels().catch(() => null)
getInsights().catch(() => null)
```

### Ключевые паттерны Frontend

Graceful degradation для optional endpoints:

```typescript
const [routesData, metricsData, comparisonData, insightsData] = await Promise.all([
  fetchRoutes(0, 100),
  getMetrics(),
  compareModels().catch(() => null),
  getInsights().catch(() => null),
])
```

Вычисление времени на ТТ:

```typescript
function visitDuration(visit: VisitScheduleItem): number | null {
  if (!visit.time_in || !visit.time_out) return null
  const [h1, m1] = visit.time_in.split(':').map(Number)
  const [h2, m2] = visit.time_out.split(':').map(Number)
  const diff = (h2 * 60 + m2) - (h1 * 60 + m1)
  return diff > 0 ? diff : null
}
```

---

## Система категорий ТТ

| Категория | % от базы | Визитов/мес | Приоритет |
|-----------|-----------|-------------|-----------|
| A | 20% | 3 | 1 (критичный) |
| B | 30% | 2 | 2 |
| C | 20% | 1 | 3 |
| D | 30% | 1/квартал | 4 |

Цветовое кодирование в Excel: A=красный, B=оранжевый, C=жёлтый, D=серый.

---

## DevOps и инфраструктура

### Docker Compose

```
Services:
  backend   -- FastAPI (порт 8000)
  frontend  -- Nginx + Vue SPA (порт 80)
  db        -- PostgreSQL 15 (порт 5432)
  redis     -- Redis 7 (порт 6379, кэш)
```

### CI/CD (GitHub Actions)

```
Триггеры: push/PR на main
Шаги:
  1. Backend тесты:  pytest backend/tests/ --cov
  2. Frontend тесты: npx vitest run
  3. TypeScript:     npx vue-tsc --noEmit
  4. Coverage report
```

### Ресурсы LLM-моделей

| Модель | Файл GGUF | RAM | Диск |
|--------|-----------|-----|------|
| Qwen2-0.5B-Instruct | qwen2-0_5b-instruct-q4_k_m.gguf | ~0.6 GB | ~400 MB |
| Llama-3.2-1B-Instruct | Llama-3.2-1B-Instruct-Q4_K_M.gguf | ~1.2 GB | ~808 MB |
| Итого | | ~1.8 GB | ~1.2 GB |

Модели загружаются **lazy** (при первом запросе) — холодный старт 5-15 сек.

---

## Тестовая архитектура

### Backend (pytest + pytest-asyncio)

```
backend/tests/
  test_llm_client.py              QwenClient / LlamaClient unit тесты
  test_qwen_client.py             Qwen-специфичные тесты
  test_llama_client.py            Llama-специфичные тесты
  test_routes.py                  API endpoint тесты
  test_integration.py             End-to-end тесты
  test_optimization_comparison.py Сравнение моделей
  test_quality_evaluator.py       Оценка качества маршрутов
```

### Frontend (Vitest + Vue Test Utils)

```
frontend/src/tests/views/
  AnalyticsView.spec.ts   9 тест-кейсов (charts, stats, import/export)
  OptimizeView.spec.ts    7 тест-кейсов (форма, модель по умолчанию)
```

Мокирование API в тестах:

```typescript
vi.mock('@/services/api', () => ({
  fetchRoutes: vi.fn(),
  getMetrics: vi.fn(),
  compareModels: vi.fn(),
  getInsights: vi.fn(),
  downloadScheduleExcel: vi.fn(),
  importScheduleExcel: vi.fn(),
}))
```

---

## Ключевые архитектурные решения

| Решение | Причина |
|---------|---------|
| Два LLM + Greedy fallback | Надёжность: всегда возвращается результат |
| `data_only=True` в openpyxl | Получаем вычисленные значения ячеек |
| Batch-загрузка VisitLog | Избегаем N+1 запросов при JOIN расписания |
| `.catch(() => null)` для optional API | Graceful degradation при отсутствии endpoint |
| `MAX_TT_PER_DAY = 14` | floor((540-30)/35) — физический лимит рабочего дня |
| Матчинг по имени в импорте | Excel не содержит UUID — матчим по rep_name + loc_name |
| AUTO ALTER TABLE в main.py | Обратная совместимость при обновлении без потери данных |
