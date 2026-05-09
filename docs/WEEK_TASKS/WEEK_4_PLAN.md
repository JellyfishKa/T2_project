# НЕДЕЛЯ 4 — УПРАВЛЕНИЕ РАСПИСАНИЕМ, АНАЛИТИКА И EXCEL-ИНТЕГРАЦИЯ

> **Статус**: ✅ Завершено
> **Период**: 24 февраля — 27 февраля 2026
> **Команда**: 3 разработчика + TL/PM
> **Методология**: Agile Lite (Kanban)

---

## Контекст и цели недели

Неделя 4 — переход от «маршрутной оптимизации» к **полноценной системе управления посещениями** торговых точек Мордовии. Основной фокус:

| Цель | Описание |
|------|----------|
| Расписание визитов | Алгоритм автоматического планирования с учётом категорий ТТ (A/B/C/D) |
| Трекинг времени на ТТ | Фактическое время прихода/ухода в VisitLog → API → UI |
| Детальный просмотр дня | Day modal с LLM-оптимизацией маршрута (3 варианта + pros/cons) |
| Форс-мажоры | Перераспределение визитов при болезни / отпуске сотрудника |
| Excel-интеграция | Экспорт расписания (6 листов) + обратный импорт с результатами |
| Аналитика | Реальная статистика по охвату ТТ, активности ТП, инсайты |

---

## Архитектурные изменения

### Новые таблицы БД

```
sales_reps         — торговые представители (id, name, status, ...)
visit_schedule     — плановые визиты (id, rep_id, location_id, planned_date, status)
visit_log          — фактические визиты (id, schedule_id, time_in, time_out, ...)
force_majeure_events — форс-мажоры (id, type, rep_id, event_date, redistributed_to)
```

### Новые backend-файлы

| Файл | Назначение |
|------|-----------|
| `src/routes/reps.py` | CRUD торговых представителей |
| `src/routes/schedule.py` | Генерация и просмотр расписания |
| `src/routes/force_majeure.py` | Регистрация и обработка форс-мажоров |
| `src/routes/visits.py` | История фактических визитов |
| `src/routes/export.py` | Excel-экспорт (6 листов) |
| `src/routes/import_excel.py` | Excel-импорт с результатами визитов |
| `src/services/schedule_planner.py` | SchedulePlanner — алгоритм планирования |
| `src/services/force_majeure_service.py` | ForceMajeureService — перераспределение |

### Новые frontend-файлы

| Файл | Назначение |
|------|-----------|
| `src/views/ScheduleView.vue` | Месячный календарь расписания |
| `src/views/RepsView.vue` | CRUD торговых представителей |

---

## BACKEND ТАСКИ — Роман Кижаев

### BE-W4-1: Модели БД — SalesRep, VisitSchedule, VisitLog, ForceMajeure

**Приоритет**: 🔴 HIGH
**Оценка**: 5 часов
**Статус**: ✅ Done

**Описание**:
Добавить новые SQLAlchemy-модели и расширить `Location` новыми полями категоризации.

**Acceptance Criteria**:
- ✅ `SalesRep` — имя, статус (`active`/`sick`/`vacation`/`unavailable`), контакты
- ✅ `VisitSchedule` — FK на `rep_id`, `location_id`, `planned_date`, `status` (5 значений)
- ✅ `VisitLog` — FK на `schedule_id`, `time_in`/`time_out` (TIME), `visited_date`
- ✅ `ForceMajeureEvent` — тип, rep_id, дата, `redistributed_to` (JSON)
- ✅ `Location` расширена: `category` (A/B/C/D), `city`, `district`, `address`
- ✅ Миграция `002_add_reps_schedule` применяется: `alembic upgrade head`
- ✅ `main.py` — AUTO ALTER TABLE для существующих БД (без потери данных)

---

### BE-W4-2: API торговых представителей (`/api/v1/reps`)

**Приоритет**: 🔴 HIGH
**Оценка**: 4 часа
**Статус**: ✅ Done

**Acceptance Criteria**:
- ✅ `GET /reps` — список с фильтром по статусу (`?status=active`)
- ✅ `POST /reps` — создание нового ТП (имя, статус)
- ✅ `PATCH /reps/{id}` — обновление статуса / имени
- ✅ `DELETE /reps/{id}` — мягкое удаление (статус `unavailable`)
- ✅ Валидация: статус только из допустимого enum
- ✅ Unit-тесты покрывают все 4 метода

---

### BE-W4-3: Алгоритм планировщика + API расписания (`/api/v1/schedule`)

**Приоритет**: 🔴 HIGH
**Оценка**: 10 часов
**Статус**: ✅ Done

**Описание**:
Ключевой функционал недели — алгоритм автоматической генерации месячного расписания с учётом категорий ТТ и рабочего времени.

**Алгоритм SchedulePlanner**:
```
Входные данные: список ТТ, список ТП, месяц, рабочие дни
Для каждой ТТ определяем кол-во визитов: A=3/мес, B=2/мес, C=1/мес, D=1/квартал
Распределяем по рабочим дням с учётом:
  - MAX_TT_PER_DAY = 14 (floor((540-30)/35))
  - Приоритет: категория A → B → C → D
  - Равномерное распределение по ТП (нагрузка)
  - Рабочие часы 09:00-18:00 (540 мин), Пн-Пт
```

**Acceptance Criteria**:
- ✅ `POST /schedule/generate` — генерирует расписание на месяц
- ✅ `GET /schedule/` — список визитов с фильтрами (месяц, ТП, ТТ, статус)
- ✅ `PATCH /schedule/{id}/status` — обновление статуса + `time_in`/`time_out`
- ✅ `GET /schedule/daily` — расписание на конкретный день
- ✅ `_schedule_to_item()` — JOIN с VisitLog → `time_in`/`time_out` в ответе
- ✅ `_load_logs_by_schedule()` — batch-загрузка VisitLog без N+1 запросов

---

### BE-W4-4: API форс-мажоров (`/api/v1/force_majeure`)

**Приоритет**: 🟡 MEDIUM
**Оценка**: 6 часов
**Статус**: ✅ Done

**Acceptance Criteria**:
- ✅ `POST /force_majeure` — регистрация события (болезнь, отпуск, авария)
- ✅ `GET /force_majeure` — список событий с фильтром по дате/ТП
- ✅ `ForceMajeureService.redistribute()` — переназначение визитов на других ТП
- ✅ `redistributed_to` — JSON с маппингом `schedule_id → new_rep_id`
- ✅ Нет перераспределения если нет свободных ТП

---

### BE-W4-5: API визитов и трекинг времени

**Приоритет**: 🟡 MEDIUM
**Оценка**: 4 часа
**Статус**: ✅ Done

**Acceptance Criteria**:
- ✅ `POST /visits` — создание VisitLog с `time_in`/`time_out`
- ✅ `GET /visits` — история с фильтром `?month=YYYY-MM&rep_id=...`
- ✅ `PATCH /schedule/{id}/status` при `status=completed` → auto-create VisitLog
- ✅ Поля `time_in`, `time_out` в ответе расписания (`HH:MM` формат)

---

### BE-W4-6: Excel экспорт (`GET /api/v1/export/schedule`)

**Приоритет**: 🔴 HIGH
**Оценка**: 6 часов
**Статус**: ✅ Done

**Описание**:
Выгрузка аналитических данных в Excel — ключевое конкурсное требование.

**Структура файла** (`t2_schedule_YYYY-MM.xlsx`):
| Лист | Содержимое |
|------|-----------|
| Расписание | Все плановые визиты с статусами и временем |
| Журнал визитов | Выполненные визиты с длительностью |
| Статистика по ТТ | Охват, % выполнения по категориям |
| Активность ТП | Выходы на маршрут, % выполнения |

**Acceptance Criteria**:
- ✅ Параметр `?month=YYYY-MM`
- ✅ Цветовые заголовки по категории (A=красный, B=оранжевый, C=жёлтый, D=серый)
- ✅ Авто-ширина колонок
- ✅ `StreamingResponse` с `Content-Disposition`

---

### BE-W4-7: Excel импорт (`POST /api/v1/import/schedule`)

**Приоритет**: 🟡 MEDIUM
**Оценка**: 5 часов
**Статус**: ✅ Done

**Описание**:
Обратная загрузка заполненного Excel с результатами визитов (статусы + время прихода/ухода).

**Acceptance Criteria**:
- ✅ Читает лист «Расписание», строки с row≥3
- ✅ Матчинг по `(planned_date, rep_name, loc_name)` — имена из Excel → ID в БД
- ✅ `STATUS_MAP` — «Выполнен» → `completed`, «Пропущен» → `skipped`, и т.д.
- ✅ При `status=completed` + наличии времени → создаёт/обновляет `VisitLog`
- ✅ Возвращает `{updated, skipped, errors[:20]}`
- ✅ Полная обработка ошибок (неверная дата, неизвестный сотрудник/ТТ/статус)

---

### BE-W4-8: Endpoint `/api/v1/optimize/variants` и `/api/v1/optimize/confirm`

**Приоритет**: 🔴 HIGH
**Оценка**: 4 часа
**Статус**: ✅ Done

**Acceptance Criteria**:
- ✅ `POST /api/v1/optimize/variants` — генерирует 3 варианта без сохранения; LLM оценивает pros/cons
- ✅ `POST /api/v1/optimize/confirm` — сохраняет выбранный вариант в БД (`routes` таблица)
- ✅ Схемы `OptimizeVariantsRequest`, `OptimizeVariantsResponse`, `ConfirmVariantRequest`
- ✅ Если LLM недоступна — варианты возвращаются без pros/cons (`llm_evaluation_success=false`)

---

## FRONTEND ТАСКИ — Владислав Наумкин

### FE-W4-1: `ScheduleView.vue` — месячный календарь

**Приоритет**: 🔴 HIGH
**Оценка**: 10 часов
**Статус**: ✅ Done

**Описание**:
Новая страница — визуальное отображение расписания визитов торговых представителей на месяц.

**Acceptance Criteria**:
- ✅ Навигация по месяцам (`<` / `>` кнопки)
- ✅ Фильтр по ТП (select из API `/reps`)
- ✅ Карточки маршрутов дня: имя ТП, кол-во ТТ, статусы
- ✅ Чип каждого визита: категория, имя ТТ, статус, длительность (`22м`)
- ✅ Кнопка «Кликнуть на день» → открывает Day modal
- ✅ Кнопка «Форс-мажор» → открывает модал

---

### FE-W4-2: `RepsView.vue` — управление сотрудниками

**Приоритет**: 🟡 MEDIUM
**Оценка**: 5 часов
**Статус**: ✅ Done

**Acceptance Criteria**:
- ✅ Список всех ТП с цветовым индикатором статуса
- ✅ Форма создания нового ТП (имя, статус)
- ✅ Inline редактирование статуса (active/sick/vacation/unavailable)
- ✅ Удаление (с подтверждением)
- ✅ Роутинг: `/reps` добавлен в `router/index.ts`
- ✅ Пункт «Сотрудники» в боковом меню

---

### FE-W4-3: Модал визита — обновление статуса + время

**Приоритет**: 🔴 HIGH
**Оценка**: 4 часа
**Статус**: ✅ Done

**Acceptance Criteria**:
- ✅ Клик на чип визита → открывает модал с деталями ТТ
- ✅ Выбор статуса: Выполнен / Пропущен / Запланирован
- ✅ Поля `time_in`, `time_out` (тип `time`, `HH:MM`) при `status=completed`
- ✅ PATCH на `schedule/{id}/status` → API обновляет БД
- ✅ После сохранения — чип показывает новый статус + длительность

---

### FE-W4-4: `visitDuration()` — вычисление длительности визита

**Приоритет**: 🟡 MEDIUM
**Оценка**: 1 час
**Статус**: ✅ Done

**Реализация**:
```typescript
function visitDuration(visit: VisitScheduleItem): number | null {
  if (!visit.time_in || !visit.time_out) return null
  const [h1, m1] = visit.time_in.split(':').map(Number)
  const [h2, m2] = visit.time_out.split(':').map(Number)
  const diff = (h2 * 60 + m2) - (h1 * 60 + m1)
  return diff > 0 ? diff : null
}
```
- ✅ Длительность в чипе визита: `(22м)`
- ✅ Длительность в модале: `⏱ Время на точке: 22 мин (10:00 — 10:22)`

---

### FE-W4-5: Day modal — детальный просмотр дня сотрудника

**Приоритет**: 🔴 HIGH
**Оценка**: 8 часов
**Статус**: ✅ Done

**Описание**:
Боковая панель с полным списком ТТ на день + LLM-оптимизация маршрута.

**Acceptance Criteria**:
- ✅ Заголовок: имя ТП, дата, кол-во ТТ
- ✅ Список визитов: категория, имя ТТ, `time_in`–`time_out` (если есть), статус
- ✅ Выбор модели: кнопки **Qwen 0.5B** / **Llama 1B**
- ✅ Кнопка «Получить варианты (ИИ)» → `POST /api/v1/optimize/variants`
- ✅ Spinner + прогресс-бар во время загрузки
- ✅ Три карточки вариантов: название, описание, метрики (км/ч/₽/%), pros/cons
- ✅ Выбор варианта кликом (выделение border-blue-500)
- ✅ Кнопка «Сохранить выбранный маршрут» → `POST /api/v1/optimize/confirm`
- ✅ Обработка ошибок: `dayOptError` с текстом под кнопкой

---

### FE-W4-6: Excel кнопки в `AnalyticsView.vue`

**Приоритет**: 🟡 MEDIUM
**Оценка**: 3 часа
**Статус**: ✅ Done

**Acceptance Criteria**:
- ✅ Кнопка «Загрузить Excel» (импорт) — `<label>` с `<input type="file" hidden>`
- ✅ Кнопка «Скачать Excel» (экспорт) — вызов `downloadScheduleExcel()`
- ✅ Spinner во время импорта/экспорта
- ✅ После импорта — блок результата: `Обновлено N, пропущено M`
- ✅ Список ошибок импорта (до 20 строк)
- ✅ После успешного импорта — перезагрузка аналитики

---

### FE-W4-7: Исправление аналитики — `compareModels` crash

**Приоритет**: 🔴 HIGH
**Оценка**: 1 час
**Статус**: ✅ Done

**Проблема**:
`compareModels()` возвращала 404 (endpoint `/benchmark/compare` удалён в неделе 3).
Так как вызов был в `Promise.all` без `.catch()` — весь `loadAnalyticsData()` падал.

**Исправление**:
```typescript
// БЫЛО (падало при 404)
const [routesData, metricsData, comparisonData] = await Promise.all([
  fetchRoutes(0, 100),
  getMetrics(),
  compareModels(),
])

// СТАЛО (graceful degradation)
const [routesData, metricsData, comparisonData, insightsData] = await Promise.all([
  fetchRoutes(0, 100),
  getMetrics(),
  compareModels().catch(() => null),
  getInsights().catch(() => null),
])
```

---

### FE-W4-8: TypeScript типы — расширение `types.ts`

**Приоритет**: 🟡 MEDIUM
**Оценка**: 2 часа
**Статус**: ✅ Done

**Новые/обновлённые типы**:
```typescript
interface SalesRep { id, name, status, ... }
interface VisitScheduleItem { ..., time_in?, time_out?, location_category? }
interface DailyRoute { rep_name, date, visits, total_tt, estimated_duration_hours }
interface MonthlyPlan { month, routes, total_visits, coverage_percent }
interface ForceMajeureEvent { id, type, rep_id, event_date, redistributed_to }
interface OptimizeVariantsResponse { variants, model_used, llm_evaluation_success }
interface ConfirmVariantRequest { name, locations, ..., original_location_ids }
interface Insights { month, total_tt, coverage_percent, category_stats, rep_activity }
```

---

## ML/ANALYTICS ТАСКИ — Дмитрий Мукасеев

### ML-W4-1: `SchedulePlanner` — алгоритм планирования

**Приоритет**: 🔴 HIGH
**Оценка**: 8 часов
**Статус**: ✅ Done

**Файл**: `backend/src/services/schedule_planner.py`

**Константы**:
```python
WORK_START_HOUR = 9          # 09:00
WORK_END_HOUR = 18           # 18:00
WORK_MINUTES = 540           # 9 часов
LUNCH_BREAK_MIN = 30
VISIT_DURATION_MIN = 15
AVG_TRAVEL_MIN_PER_TT = 20
SLOT_MIN = VISIT_DURATION_MIN + AVG_TRAVEL_MIN_PER_TT  # 35 мин
MAX_TT_PER_DAY = floor((WORK_MINUTES - LUNCH_BREAK_MIN) / SLOT_MIN)  # 14
```

**Логика категорий**:
```
A: 3 визита/месяц, приоритет 1 (критичная частота)
B: 2 визита/месяц, приоритет 2
C: 1 визит/месяц, приоритет 3
D: 1 визит/квартал → в текущем месяце только если нет переполнения
```

**Acceptance Criteria**:
- ✅ `generate_monthly_plan(month, rep_ids, location_ids)` → список `VisitSchedule`
- ✅ Равномерное распределение нагрузки между ТП
- ✅ Не превышает `MAX_TT_PER_DAY` на одного ТП в день
- ✅ Только рабочие дни (Mon-Fri), без праздников
- ✅ `_next_working_day()` — вспомогательная функция

---

### ML-W4-2: `ForceMajeureService` — перераспределение визитов

**Приоритет**: 🟡 MEDIUM
**Оценка**: 5 часов
**Статус**: ✅ Done

**Файл**: `backend/src/services/force_majeure_service.py`

**Логика**:
1. Получить все запланированные визиты пострадавшего ТП на указанный период
2. Найти доступных ТП (статус `active`, не перегруженных в день визита)
3. Переназначить визиты (`rep_id` в `VisitSchedule`) с записью в `redistributed_to`

**Acceptance Criteria**:
- ✅ Корректное перераспределение при 1 недоступном ТП
- ✅ Нет перераспределения если все ТП заняты (возвращает предупреждение)
- ✅ `redistributed_to` JSON: `{"schedule_id": "new_rep_id", ...}`

---

### ML-W4-3: Сервис инсайтов — реальная аналитика

**Приоритет**: 🔴 HIGH
**Оценка**: 6 часов
**Статус**: ✅ Done

**Файл**: `backend/src/routes/insights.py` (полная переработка)

**Ответ `GET /api/v1/insights?month=YYYY-MM`**:
```json
{
  "month": "2026-02",
  "total_tt": 250,
  "covered_tt": 198,
  "coverage_percent": 79.2,
  "category_stats": {
    "A": {"planned": 60, "completed": 57, "pct": 95.0},
    "B": {"planned": 80, "completed": 72, "pct": 90.0},
    "C": {"planned": 35, "completed": 28, "pct": 80.0},
    "D": {"planned": 23, "completed": 18, "pct": 78.3}
  },
  "rep_activity": [
    {"rep_name": "Иванов", "outings": 20, "completed": 45, "total": 48}
  ]
}
```

**Acceptance Criteria**:
- ✅ Параметр `?month=YYYY-MM` обязателен
- ✅ `coverage_percent` = кол-во уникальных посещённых ТТ / всего ТТ × 100
- ✅ `category_stats` по каждой категории A/B/C/D
- ✅ `rep_activity` — выходы на маршрут (уникальные дни) + % выполнения

---

### ML-W4-4: Датасет 250 ТТ Мордовии

**Приоритет**: 🟡 MEDIUM
**Оценка**: 3 часа
**Статус**: ✅ Done

**Файл**: `scripts/generate_mordovia_dataset.py`

**Acceptance Criteria**:
- ✅ 250 торговых точек с реалистичными данными
- ✅ 22 района + Саранск = 23 зоны
- ✅ Распределение категорий: A=20%, B=30%, C=20%, D=30%
- ✅ Координаты в пределах Мордовии (lat ~54.2, lon ~44.1)
- ✅ Выход: `data/locations_mordovia_250.json`

---

### ML-W4-5: Оптимизация вариантов маршрута (3 варианта)

**Приоритет**: 🔴 HIGH
**Оценка**: 5 часов
**Статус**: ✅ Done

**Файл**: `backend/src/services/optimize.py` — метод `generate_variants()`

**Алгоритм**:
```
Вариант 1: «По категориям» — A → B → C → D (приоритетный)
Вариант 2: «Минимальное расстояние» — nearest-neighbor (классический)
Вариант 3: «Сбалансированный» — гибридный (учёт и расстояния, и приоритета)
```

**Acceptance Criteria**:
- ✅ LLM оценивает каждый вариант: pros/cons + `quality_score`
- ✅ Если LLM недоступна — `llm_evaluation_success=false`, варианты без оценки
- ✅ Схема `OptimizeVariantsResponse` с `variants[].pros`, `variants[].cons`

---

## QA/PM ТАСКИ — Сергей Маклаков

### QA-W4-1: CI — обновление тестов `AnalyticsView.spec.ts`

**Приоритет**: 🔴 HIGH
**Оценка**: 2 часа
**Статус**: ✅ Done

**Проблема**:
После добавления `getInsights`, `downloadScheduleExcel`, `importScheduleExcel` в `AnalyticsView.vue`, тест-файл не мокировал эти функции → CI падал.

**Исправление в `vi.mock`**:
```typescript
vi.mock('@/services/api', () => ({
  fetchRoutes: vi.fn(),
  getMetrics: vi.fn(),
  compareModels: vi.fn(),
  getInsights: vi.fn(),          // ← добавлено
  downloadScheduleExcel: vi.fn(), // ← добавлено
  importScheduleExcel: vi.fn(),   // ← добавлено
}))
```

**В `beforeEach`**:
```typescript
vi.mocked(api.getInsights).mockResolvedValue(null as any)
vi.mocked(api.downloadScheduleExcel).mockResolvedValue(undefined)
vi.mocked(api.importScheduleExcel).mockResolvedValue({ updated: 0, skipped: 0, errors: [] })
```

---

### QA-W4-2: CI — исправление `OptimizeView.spec.ts`

**Приоритет**: 🔴 HIGH
**Оценка**: 1 час
**Статус**: ✅ Done

**Проблема**:
Тест ожидал `llama` как модель по умолчанию, но `OptimizeView.vue` установил `qwen` дефолтом.

**Исправление**:
```typescript
// БЫЛО
it('выбирает Llama модель по умолчанию', async () => {
  expect(wrapper.find('input[value="llama"]').element.checked).toBe(true)
})

// СТАЛО
it('выбирает Qwen модель по умолчанию', async () => {
  expect(wrapper.find('input[value="qwen"]').element.checked).toBe(true)
})
```

---

### QA-W4-3: Обновление документации

**Приоритет**: 🟡 MEDIUM
**Оценка**: 4 часа
**Статус**: ✅ Done

**Acceptance Criteria**:
- ✅ `docs/WEEK_TASKS/WEEK_4_PLAN.md` — этот документ
- ✅ `docs/PLANS/TEST_PLAN_WEEK4.md` — тест-план
- ✅ `README.md` — обновлён: структура репозитория, API endpoints, статус проекта

---

## Итоговая таблица задач

| ID | Исполнитель | Задача | Часы | Приоритет | Статус |
|----|-------------|--------|------|-----------|--------|
| BE-W4-1 | Роман | Модели БД (4 новые таблицы) | 5 | 🔴 HIGH | ✅ |
| BE-W4-2 | Роман | API `/reps` (CRUD) | 4 | 🔴 HIGH | ✅ |
| BE-W4-3 | Роман | SchedulePlanner + API `/schedule` | 10 | 🔴 HIGH | ✅ |
| BE-W4-4 | Роман | API `/force_majeure` + redistribution | 6 | 🟡 MED | ✅ |
| BE-W4-5 | Роман | API `/visits` + time tracking | 4 | 🟡 MED | ✅ |
| BE-W4-6 | Роман | Excel экспорт (6 листов) | 6 | 🔴 HIGH | ✅ |
| BE-W4-7 | Роман | Excel импорт (status + time) | 5 | 🟡 MED | ✅ |
| BE-W4-8 | Роман | `/api/v1/optimize/variants` + `/api/v1/optimize/confirm` | 4 | 🔴 HIGH | ✅ |
| FE-W4-1 | Владислав | `ScheduleView.vue` — календарь | 10 | 🔴 HIGH | ✅ |
| FE-W4-2 | Владислав | `RepsView.vue` — CRUD | 5 | 🟡 MED | ✅ |
| FE-W4-3 | Владислав | Модал визита (статус + время) | 4 | 🔴 HIGH | ✅ |
| FE-W4-4 | Владислав | `visitDuration()` + чип/модал | 1 | 🟡 MED | ✅ |
| FE-W4-5 | Владислав | Day modal (LLM варианты) | 8 | 🔴 HIGH | ✅ |
| FE-W4-6 | Владислав | Excel кнопки в AnalyticsView | 3 | 🟡 MED | ✅ |
| FE-W4-7 | Владислав | Fix analytics crash | 1 | 🔴 HIGH | ✅ |
| FE-W4-8 | Владислав | TypeScript типы | 2 | 🟡 MED | ✅ |
| ML-W4-1 | Дмитрий | SchedulePlanner алгоритм | 8 | 🔴 HIGH | ✅ |
| ML-W4-2 | Дмитрий | ForceMajeureService | 5 | 🟡 MED | ✅ |
| ML-W4-3 | Дмитрий | Insights аналитика (реальная) | 6 | 🔴 HIGH | ✅ |
| ML-W4-4 | Дмитрий | Датасет 250 ТТ Мордовии | 3 | 🟡 MED | ✅ |
| ML-W4-5 | Дмитрий | Генерация 3 вариантов маршрута | 5 | 🔴 HIGH | ✅ |
| QA-W4-1 | Сергей | CI fix: AnalyticsView тесты | 2 | 🔴 HIGH | ✅ |
| QA-W4-2 | Сергей | CI fix: OptimizeView тест | 1 | 🔴 HIGH | ✅ |
| QA-W4-3 | Сергей | Обновление документации | 4 | 🟡 MED | ✅ |
| | | **ИТОГО** | **~112 ч** | | |

---

## Тестовое покрытие по итогам недели 4

| Компонент | Тестов | Статус CI |
|-----------|--------|-----------|
| Backend (pytest) | 61 | ✅ Passing |
| Frontend (vitest) | 182 | ✅ Passing |
| ML | 15 | ✅ Passing |
| TypeScript type-check | — | ✅ 0 ошибок |

---

## Конкурсные требования — статус выполнения

| Требование из PDF | Реализовано в неделе 4 |
|---|---|
| Расчёт маршрутов с минимизацией километража | ✅ `/api/v1/optimize` + `/api/v1/optimize/variants` (3 варианта) |
| Учёт рабочего времени (9–18) | ✅ SchedulePlanner: 540 мин, Пн-Пт |
| Сегментация ТТ по категориям A/B/C/D | ✅ Частота визитов: A=3, B=2, C=1, D=1/квартал |
| 100% охват базы ТТ | ✅ Insights: `coverage_percent` |
| Форс-мажоры + перераспределение | ✅ ForceMajeureService + API |
| **Отчёт о времени нахождения на каждой ТТ** | ✅ `time_in`/`time_out` в VisitLog + UI |
| **Детализация по времени и дате посещения** | ✅ VisitLog + Журнал визитов (Excel лист 2) |
| **Количество выходов ТП на маршрут** | ✅ Insights + Excel лист «Активность ТП» |
| **Выгрузка аналитической информации** | ✅ Excel 6 листов + Excel импорт |

---

## Следующие шаги (Неделя 5+)

1. Финальное демо для жюри конкурса
2. Нагрузочное тестирование (250 ТТ × 5 ТП = реальный датасет)
3. Мониторинг и логирование в продакшене
