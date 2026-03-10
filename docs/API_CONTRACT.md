# КОНТРАКТ API

**Соглашение Frontend-Backend по структуре API**

> Последнее обновление: 10 марта 2026

---

## Обзор

Этот документ определяет контракт между Frontend и Backend.
**Frontend использует это для создания mock interceptors.**
**Backend реализует ровно это.**

**Базовый URL**:
```
Разработка: http://localhost:8000/api/v1
Production:  http://<server-ip>/api/v1
```

---

## Основные модели данных

### Location (Торговая точка)

```json
{
  "id": "store-123",
  "name": "Магазин Саранск-1",
  "lat": 54.187,
  "lon": 45.183,
  "address": "г. Саранск, ул. Победы, 12",
  "city": "Саранск",
  "district": "Октябрьский",
  "category": "A",
  "time_window_start": "09:00",
  "time_window_end": "18:00"
}
```

> **Важно**: поля координат — `lat`/`lon` (не `latitude`/`longitude`)

---

### SalesRep (Торговый представитель)

```json
{
  "id": "rep-001",
  "name": "Иванов А.А.",
  "status": "active",
  "created_at": "2026-01-15T08:00:00Z",
  "warning": null,
  "pending_visits_count": 0
}
```

Допустимые значения `status`: `active` | `sick` | `vacation` | `unavailable`

> **Новое (v1.2.0)**: При `PATCH /reps/{id}` с `status=sick` или `status=vacation` — в ответе могут присутствовать:
> - `warning`: строка с предупреждением о незакрытых визитах
> - `pending_visits_count`: кол-во плановых будущих визитов сотрудника

---

### VisitScheduleItem (Плановый визит)

```json
{
  "id": "sched-456",
  "location_id": "store-123",
  "location_name": "Магазин Саранск-1",
  "location_category": "A",
  "rep_id": "rep-001",
  "rep_name": "Иванов А.А.",
  "planned_date": "2026-02-13",
  "status": "completed",
  "time_in": "10:00",
  "time_out": "10:22"
}
```

Допустимые значения `status`: `planned` | `completed` | `skipped` | `cancelled` | `rescheduled`

---

### DailyRoute (Маршрут дня)

```json
{
  "date": "2026-02-13",
  "rep_id": "rep-001",
  "rep_name": "Иванов А.А.",
  "visits": [...],
  "total_tt": 12,
  "estimated_duration_hours": 7.2,
  "lunch_break_at": "13:00"
}
```

---

### VisitLog (Фактический визит)

```json
{
  "id": "log-101",
  "location_id": "store-123",
  "rep_id": "rep-001",
  "visited_date": "2026-02-13",
  "schedule_id": "sched-456",
  "time_in": "10:00:00",
  "time_out": "10:22:00",
  "notes": null,
  "created_at": "2026-02-13T10:22:05Z"
}
```

---

### Route (Оптимизированный маршрут)

```json
{
  "id": "route-456",
  "name": "Маршрут 1 — День 1",
  "locations": ["store-1", "store-2", "store-3"],
  "total_distance_km": 45.3,
  "total_time_hours": 2.5,
  "total_cost_rub": 1500,
  "model_used": "qwen",
  "fallback_reason": null,
  "created_at": "2026-02-13T10:30:00Z"
}
```

---

### OptimizeVariant (Вариант маршрута)

```json
{
  "id": 1,
  "name": "По категориям",
  "description": "Приоритет A→B→C→D, оптимально для срочных задач",
  "locations": [
    {"id": "store-1", "name": "ТТ-1", "category": "A", "lat": 54.19, "lon": 45.18}
  ],
  "metrics": {
    "distance_km": 42.5,
    "time_hours": 6.1,
    "cost_rub": 850,
    "quality_score": 88.5
  },
  "pros": ["Все A-категории обработаны первыми", "Минимальный риск пропуска"],
  "cons": ["Километраж не оптимален"]
}
```

---

### OptimizeVariantsResponse

```json
{
  "variants": [<OptimizeVariant>, <OptimizeVariant>, <OptimizeVariant>],
  "model_used": "qwen",
  "llm_evaluation_success": true
}
```

---

### ForceMajeureEvent (Форс-мажор)

```json
{
  "id": "fm-789",
  "type": "illness",
  "rep_id": "rep-001",
  "rep_name": "Иванов А.А.",
  "event_date": "2026-02-20",
  "description": "Грипп, больничный лист",
  "affected_tt_count": 7,
  "redistributed_to": [
    {
      "rep_id": "rep-002",
      "rep_name": "Петров В.В.",
      "location_ids": ["store-1", "store-2", "store-3", "store-4"],
      "new_date": "2026-02-21"
    },
    {
      "rep_id": "rep-003",
      "rep_name": "Сидоров С.С.",
      "location_ids": ["store-5", "store-6", "store-7"],
      "new_date": "2026-02-21"
    }
  ],
  "created_at": "2026-02-20T07:30:00Z"
}
```

Допустимые значения `type`: `illness` | `weather` | `vehicle_breakdown` | `other`

---

### Metric (Метрика LLM)

```json
{
  "id": "metric-789",
  "route_id": "route-456",
  "model": "qwen",
  "response_time_ms": 1250,
  "quality_score": 85.0,
  "cost_rub": 25.50,
  "timestamp": "2026-02-13T10:30:00Z"
}
```

---

### Insights (Аналитика охвата)

```json
{
  "month": "2026-02",
  "total_tt": 250,
  "coverage_pct": 79.2,
  "visits_this_month": {
    "planned": 198,
    "completed": 157,
    "completion_rate": 79.3
  },
  "by_category": {
    "A": {"total": 50, "planned": 150, "completed": 143, "pct": 95.3},
    "B": {"total": 75, "planned": 150, "completed": 135, "pct": 90.0},
    "C": {"total": 50, "planned": 50, "completed": 40, "pct": 80.0},
    "D": {"total": 75, "planned": 75, "completed": 60, "pct": 80.0}
  },
  "by_district": [
    {"district": "Саранск", "total": 50, "coverage_pct": 88.0}
  ],
  "rep_activity": [
    {
      "rep_id": "rep-001",
      "rep_name": "Иванов А.А.",
      "outings_count": 20,
      "tt_visited": 45
    }
  ],
  "force_majeure_count": 2
}
```

---

## Endpoints

### Оптимизация маршрутов

#### `POST /optimize`

Оптимизация с авто-fallback (Qwen → Llama → Greedy).

**Request**:
```json
{
  "location_ids": ["store-1", "store-2", "store-3"],
  "model": "auto"
}
```

**Response** `200`:
```json
{
  "id": "route-456",
  "name": "Оптимизированный маршрут",
  "locations": ["store-2", "store-1", "store-3"],
  "total_distance_km": 42.5,
  "total_time_hours": 6.1,
  "total_cost_rub": 850,
  "model_used": "qwen",
  "quality_score": 88.5,
  "response_time_ms": 1250,
  "fallback_reason": null,
  "created_at": "2026-02-13T10:30:00Z"
}
```

**Errors**: `404` — locations not found | `500` — optimization failed

---

#### `POST /optimize/variants`

Генерация 3 вариантов маршрута без сохранения.

**Request**:
```json
{
  "location_ids": ["store-1", "store-2", "store-3", "store-4"],
  "model": "qwen"
}
```

**Response** `200`: `OptimizeVariantsResponse`

**Errors**: `422` — менее 2 точек | `404` — locations not found

---

#### `POST /optimize/confirm`

Сохранение выбранного варианта в БД.

**Request**:
```json
{
  "name": "Иванов — 2026-02-13 (По категориям)",
  "locations": ["store-2", "store-1", "store-3"],
  "total_distance_km": 42.5,
  "total_time_hours": 6.1,
  "total_cost_rub": 850,
  "quality_score": 88.5,
  "model_used": "qwen",
  "original_location_ids": ["store-1", "store-2", "store-3"]
}
```

**Response** `200`: `Route` (полная схема с `id`, `created_at`)

---

#### `POST /qwen/optimize`

Прямой вызов Qwen. Response идентичен `/optimize`.

#### `POST /llama/optimize`

Прямой вызов Llama. Response идентичен `/optimize`.

---

### Торговые представители

#### `GET /reps`

```
Query params: ?status=active
```

**Response** `200`: `[<SalesRep>, ...]` (плоский массив)

#### `POST /reps`

**Request**: `{"name": "Петров В.В.", "status": "active"}`

**Response** `201`: `SalesRep`

#### `PATCH /reps/{id}`

**Request**: `{"status": "sick"}` или `{"name": "Новое имя"}`

**Response** `200`: обновлённый `SalesRep` с полями `warning` и `pending_visits_count`

> **v1.2.0**: При переводе в `sick` или `vacation` — ответ содержит `warning` (строка предупреждения о незакрытых визитах) и `pending_visits_count` (кол-во плановых будущих визитов).

**Errors**: `404` — не найден | `422` — недопустимый статус

#### `DELETE /reps/{id}`

**Response** `204 No Content`

---

### Расписание визитов

#### `POST /schedule/generate`

Генерация месячного плана визитов.

```
Query params: ?force=false   (true — удалить существующие planned и создать заново)
```

**Request**:
```json
{
  "month": "2026-02",
  "rep_ids": ["rep-001", "rep-002"]
}
```

**Response** `201`:
```json
{
  "month": "2026-02",
  "total_visits_planned": 248,
  "total_tt_planned": 198,
  "total_locations": 250,
  "coverage_pct": 79.2,
  "reps_count": 4
}
```

**Errors**: `409` — расписание уже существует (при `force=false`):
```json
{
  "message": "Расписание на 2026-02 уже существует (248 плановых визитов). Используйте ?force=true для перегенерации.",
  "existing_count": 248
}
```

---

#### `GET /schedule/`

```
Query params: ?month=2026-02   (обязательный)
              &rep_id=rep-001  (опционально)
              &from_date=2026-02-10  (опционально, YYYY-MM-DD)
              &to_date=2026-02-20    (опционально, YYYY-MM-DD)
```

**Response** `200`: `MonthlyPlan`
```json
{
  "month": "2026-02",
  "routes": [<DailyRoute>, ...],
  "total_tt_planned": 248,
  "coverage_pct": 79.2
}
```

> `time_in` и `time_out` в `VisitScheduleItem` заполнены если существует `VisitLog` для этого визита.
>
> **v1.2.0**: `from_date` / `to_date` фильтруют визиты внутри месяца.

---

#### `PATCH /schedule/{id}`

Обновление статуса визита (и опционально — времени).

**Request**:
```json
{
  "status": "completed",
  "time_in": "10:00",
  "time_out": "10:22"
}
```

**Response** `200`: обновлённый `VisitScheduleItem`

> При `status=completed` + наличии `time_in`/`time_out` → создаётся `VisitLog`.

#### State Machine (v1.2.0)

| Текущий статус | Допустимые переходы |
|----------------|---------------------|
| `planned` | `completed`, `skipped`, `cancelled`, `rescheduled` |
| `skipped` | `planned`, `cancelled` |
| `rescheduled` | `completed`, `skipped`, `cancelled` |
| `completed` | — (заблокировано) |
| `cancelled` | — (заблокировано) |

**Errors**: `422` — недопустимый переход статуса:
```json
{
  "message": "Переход 'completed' → 'planned' не разрешён.",
  "current_status": "completed",
  "requested_status": "planned",
  "allowed_transitions": []
}
```

---

---

### Форс-мажоры

#### `POST /force_majeure`

**Request**:
```json
{
  "type": "illness",
  "rep_id": "rep-001",
  "event_date": "2026-02-20",
  "description": "Больничный лист"
}
```

**Response** `201`: `ForceMajeureEvent`

---

#### `GET /force_majeure`

```
Query params: ?month=2026-02&rep_id=rep-001
```

**Response** `200`: `{"total": N, "items": [<ForceMajeureEvent>, ...]}`

---

### История визитов

#### `POST /visits`

**Request**:
```json
{
  "schedule_id": "sched-456",
  "rep_id": "rep-001",
  "location_id": "store-123",
  "visited_date": "2026-02-13",
  "time_in": "10:00",
  "time_out": "10:22"
}
```

**Response** `201`: созданная запись `VisitLog`

---

#### `GET /visits`

```
Query params: ?month=2026-02&rep_id=rep-001   (month обязательный)
```

**Response** `200`: `[<VisitLog>, ...]` (плоский массив, отсортирован по visited_date)

---

### Локации

#### `GET /locations/`

```
Query params: ?category=A&city=Саранск&limit=100&offset=0
```

**Response** `200`: `{"total": N, "items": [<Location>, ...]}`

#### `POST /locations/`

**Request**: `Location` без `id`

**Response** `201`: `Location` с `id`

#### `POST /locations/upload`

Загрузка CSV/JSON файла с локациями.

**Response** `200`: `{"created": N, "skipped": M, "errors": [...]}`

---

### Аналитика и инсайты

#### `GET /metrics`

```
Query params: ?model=qwen&limit=100
```

**Response** `200`: `{"total": N, "metrics": [<Metric>, ...]}`

---

#### `GET /insights`

```
Query params: ?month=2026-02   (обязательный)
```

**Response** `200`: `Insights`

---

#### `GET /routes/`

```
Query params: ?limit=100&offset=0
```

**Response** `200`:
```json
{
  "total": 42,
  "items": [<Route>, ...]
}
```

#### `GET /routes/{id}`

**Response** `200`: `Route` + `metrics: [<Metric>]`

---

### Excel экспорт / импорт

#### `GET /export/schedule`

```
Query params: ?month=2026-02   (обязательный)
```

**Response** `200`:
- `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- `Content-Disposition: attachment; filename="t2_schedule_2026-02.xlsx"`

Структура файла (5 листов):

| Лист | Содержимое |
|------|-----------|
| Расписание | Все плановые визиты (дата, ТП, ТТ, статус, время) |
| Журнал визитов | Выполненные визиты с длительностью (мин) |
| Статистика по ТТ | Охват, плановые/выполненные/пропущенные, % |
| Активность ТП | Выходы на маршрут, % выполнения |
| Журнал изменений | AuditLog за месяц: смена статусов, форс-мажоры, генерации |

---

#### `POST /import/schedule`

Загрузка заполненного Excel с результатами визитов.

**Request**: `multipart/form-data`, поле `file` — `.xlsx` файл

**Response** `200`:
```json
{
  "updated": 45,
  "skipped": 3,
  "errors": [
    "Стр.5: сотрудник 'Неизвестный' не найден",
    "Стр.12: неизвестный статус 'Отработан'"
  ]
}
```

> Максимум 20 ошибок в ответе. Файл должен быть экспортирован через `/export/schedule`.

**Errors**: `400` — нечитаемый файл | `500` — openpyxl не установлен

---

### Системные

#### `GET /health` и `GET /api/v1/health`

**Response** `200` (v1.2.0):
```json
{
  "status": "healthy",
  "database": "connected",
  "services": {
    "database": "connected",
    "qwen": "loaded",
    "llama": "not_loaded"
  },
  "disk_free_mb": 4200,
  "visits_today": 12,
  "version": "1.2.0"
}
```

Значения `qwen`/`llama`: `"loaded"` | `"not_loaded"` | `"error"`

**Response** `503` — если БД недоступна.

---

## Коды ошибок

| Код | Значение |
|-----|---------|
| 400 | Неверный запрос (формат, параметры) |
| 404 | Ресурс не найден |
| 409 | Конфликт — например, расписание уже существует (`POST /schedule/generate`) |
| 422 | Недопустимое действие — invalid state machine transition, ошибка валидации |
| 500 | Внутренняя ошибка сервера |
| 503 | Сервис недоступен (БД, модели) |

> **409 (Conflict)** при `POST /schedule/generate?force=false`:
> ```json
> {"detail": {"message": "...", "existing_count": 248}}
> ```
>
> **422 (Unprocessable)** при `PATCH /schedule/{id}` с недопустимым переходом:
> ```json
> {"detail": {"message": "Переход 'completed' → 'planned' не разрешён.", "current_status": "completed", "requested_status": "planned", "allowed_transitions": []}}
> ```

Формат ошибки:
```json
{"detail": "Описание ошибки"}
```

---

## Полный список endpoints (Неделя 4)

| Метод | Путь | Тег | Статус |
|-------|------|-----|--------|
| GET | `/health` | System | ✅ |
| GET | `/api/v1/health` | System | ✅ |
| GET | `/api/v1/locations/` | Locations | ✅ |
| POST | `/api/v1/locations/` | Locations | ✅ |
| POST | `/api/v1/locations/upload` | Locations | ✅ |
| POST | `/api/v1/optimize` | Optimization | ✅ |
| POST | `/api/v1/optimize/variants` | Optimization | ✅ |
| POST | `/api/v1/optimize/confirm` | Optimization | ✅ |
| POST | `/api/v1/qwen/optimize` | Qwen | ✅ |
| POST | `/api/v1/llama/optimize` | Llama | ✅ |
| GET | `/api/v1/metrics` | Metrics | ✅ |
| GET | `/api/v1/insights` | Insights | ✅ |
| GET | `/api/v1/routes/` | Routes | ✅ |
| GET | `/api/v1/routes/{id}` | Routes | ✅ |
| GET | `/api/v1/reps` | Reps | ✅ |
| POST | `/api/v1/reps` | Reps | ✅ |
| PATCH | `/api/v1/reps/{id}` | Reps | ✅ |
| DELETE | `/api/v1/reps/{id}` | Reps | ✅ |
| POST | `/api/v1/schedule/generate` | Schedule | ✅ |
| GET | `/api/v1/schedule/` | Schedule | ✅ |
| PATCH | `/api/v1/schedule/{id}/status` | Schedule | ✅ |
| POST | `/api/v1/force_majeure` | ForceMajeure | ✅ |
| GET | `/api/v1/force_majeure` | ForceMajeure | ✅ |
| POST | `/api/v1/visits` | Visits | ✅ |
| GET | `/api/v1/visits` | Visits | ✅ |
| GET | `/api/v1/export/schedule` | Export | ✅ |
| POST | `/api/v1/import/schedule` | Import | ✅ |

> Swagger UI с полной документацией: `http://localhost:8000/docs`
