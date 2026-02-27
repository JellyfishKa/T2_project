# T2 Project — Полный план перестройки сервиса

> Версия: 1.0 | Дата: 26.02.2026  
> Составлен на основе: Excel-файла организатора, PDF с функциональными требованиями,  
> технического анализа существующего кода

---

## 1. Исходные требования организатора

### 1.1 База торговых точек (ТТ)

**Источник:** `data/organizer_example.xlsx`

#### Распределение по районам Мордовии

| Территория | Кол-во ТТ |
|---|---|
| г.о. Саранск | 30 |
| Ардатовский район | 10 |
| Атяшевский район | 10 |
| Атюрьевский район | 10 |
| Большеберезниковский район | 10 |
| Большеигнатовский район | 10 |
| Дубёнский район | 10 |
| Ельниковский район | 10 |
| Зубово-Полянский район | 10 |
| Инсарский район | 10 |
| Ичалковский район | 10 |
| Кадошкинский район | 10 |
| Ковылкинский район | 10 |
| Кочкуровский район | 10 |
| Краснослободский район | 10 |
| Лямбирский район | 10 |
| Ромодановский район | 10 |
| Рузаевский район | 10 |
| Старошайговский район | 10 |
| Темниковский район | 10 |
| Теньгушевский район | 10 |
| Торбеевский район | 10 |
| Чамзинский район | 10 |
| **Итого** | **250** |

#### Категории ТТ и частота посещений

| Категория | Характеристика | Доля | Кол-во ТТ | Частота посещений |
|---|---|---|---|---|
| **A** | Крупные точки торговли с долей не 5 кол-раз | 20% | 50 | **3 раза в месяц** |
| **B** | Средние точки торговли с долей не 3 кол-раз | 30% | 75 | **2 раза в месяц** |
| **C** | Мелкие точки торговли с долей не 1 кол-раз | 20% | 50 | **1 раз в месяц** |
| **D** | Минорные точки торговли с частотой не 1 кол-раз | 30% | 75 | **1 раз в квартал** |

#### Условия работы торговой команды

- Количество сотрудников: **4 на район** (торговые представители, не машины)
- Режим работы: **5 дней в неделю, с 9:00 до 18:00**
- Сотрудники **не привязаны жёстко к конкретному району** — могут работать в любом

---

## 2. Функциональные требования (из PDF)

### 2.1 Формирование оптимизированных маршрутов на основе базы ТТ

1. Расчёт маршрутов с **минимизацией километража**
2. Учёт **рабочего времени** торговых представителей (соблюдение графика, лимитов рабочего дня)
3. **Сегментация ТТ по категориям (A, B, C, D)** с учётом приоритетности посещения
4. Гарантия **100% охвата** всей базы ТТ, включая механизм добавления ТТ из пройденного
   маршрута в случае, если точка не работала в запланированный день

### 2.2 Учёт непредвиденных обстоятельств (форс-мажоров)

1. Анализ и учёт факторов, влияющих на выполнение маршрута:
   - **Человеческий фактор** (болезнь, непредвиденные обстоятельства у торгового представителя)
   - **Погодные условия**
   - **Техническая неисправность автотранспорта**
2. Автоматизированный механизм **перераспределения ТТ** на другие дни в случае
   невозможности выполнения маршрута по вышеуказанным причинам

**Реакция системы:** В случае отмены маршрута, все запланированные на этот день ТТ должны
быть автоматически и **равномерно перераспределены** по маршрутам других сотрудников
на ближайшие доступные дни.

### 2.3 Функционал выгрузки аналитической информации

1. Статистика по **посещаемости ТТ**
2. Отчёт о **времени нахождения торгового представителя** на каждой ТТ
3. **Детализация по времени и дате посещения** каждой точки
4. Учёт **количества выходов торгового представителя** на маршрут

**Ожидаемый результат:** Программа-отчёт, которая станет инструментом для эффективного
планирования маршрутов торговой команды.

---

## 3. Диагноз текущего состояния кода

### 3.1 Критические проблемы

| # | Проблема | Файл | Строка |
|---|---|---|---|
| 1 | `priority` захардкожен как `"A"` для всех ТТ | `services/optimize.py` | ~47 |
| 2 | Категории A/B/C/D только в промпте LLM, алгоритмически не применяются | `services/optimize.py` | — |
| 3 | Частота посещений (3x/мес, 2x/мес, 1x/кв.) нигде не реализована | — | — |
| 4 | В БД нет полей `category`, `city`, `district`, `address` у Location | `database/models.py` | — |
| 5 | Оптимизация: всегда одна машина, один маршрут — нет VRP | `services/optimize.py` | — |
| 6 | Форс-мажоры не существуют как концепция в коде | — | — |
| 7 | `/insights` возвращает пустышку (только рекомендацию модели) | `routes/insights.py` | — |
| 8 | Датасет Мордовии: 30 ТТ вместо нужных 250, без распределения по категориям | `data/` | — |
| 9 | LLM-вывод полностью игнорируется, greedy всегда перезаписывает | `services/optimize.py` | — |
| 10 | Сотрудников как сущности нет вообще | — | — |

### 3.2 Несоответствия фронтенд ↔ бэкенд

| Поле | Фронтенд | Бэкенд |
|---|---|---|
| `Location.priority` | `number` | `"A"/"B"/"C"/"D"` (строка) |
| `Location` координаты | `latitude`/`longitude` | `lat`/`lon` |
| `RouteDetails` | ожидает `locations_sequence`, `locations_data` | не возвращает эти поля |
| `/insights` | ожидает полную структуру аналитики | возвращает только строку |

---

## 4. Новая архитектура данных

### 4.1 Обновлённая таблица `locations`

```sql
-- Добавляемые поля к существующей таблице
ALTER TABLE locations ADD COLUMN category    VARCHAR(1);   -- A | B | C | D
ALTER TABLE locations ADD COLUMN city        VARCHAR(255);
ALTER TABLE locations ADD COLUMN district    VARCHAR(255); -- Саранск, Ардатовский р-н, ...
ALTER TABLE locations ADD COLUMN address     VARCHAR(500);
Правило для category:

A → приоритет 1, посещение 3 раза в месяц
B → приоритет 2, посещение 2 раза в месяц
C → приоритет 3, посещение 1 раз в месяц
D → приоритет 4, посещение 1 раз в квартал
4.2 Новая таблица sales_reps (Сотрудники)
CREATE TABLE sales_reps (
    id          VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR NOT NULL,         -- ФИО торгового представителя
    status      VARCHAR NOT NULL          -- active | sick | vacation | unavailable
                DEFAULT 'active',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
Примечание: Сотрудники создаются вручную через UI администратором. Сотрудники не привязаны к конкретному району — могут работать везде.

4.3 Новая таблица visit_schedule (Плановые визиты)
CREATE TABLE visit_schedule (
    id              VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id     VARCHAR NOT NULL REFERENCES locations(id),
    rep_id          VARCHAR NOT NULL REFERENCES sales_reps(id),
    planned_date    DATE NOT NULL,
    status          VARCHAR NOT NULL     -- planned | completed | skipped | rescheduled | cancelled
                    DEFAULT 'planned',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
4.4 Новая таблица visit_log (Фактические визиты)
CREATE TABLE visit_log (
    id              VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_id     VARCHAR REFERENCES visit_schedule(id),  -- nullable (незапланированный)
    location_id     VARCHAR NOT NULL REFERENCES locations(id),
    rep_id          VARCHAR NOT NULL REFERENCES sales_reps(id),
    visited_date    DATE NOT NULL,
    time_in         TIME,
    time_out        TIME,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
4.5 Новая таблица force_majeure_events (Форс-мажоры)
CREATE TABLE force_majeure_events (
    id                  VARCHAR PRIMARY KEY DEFAULT gen_random_uuid(),
    type                VARCHAR NOT NULL,   -- illness | weather | vehicle_breakdown | other
    rep_id              VARCHAR NOT NULL REFERENCES sales_reps(id),
    event_date          DATE NOT NULL,
    description         TEXT,
    affected_tt_ids     JSON DEFAULT '[]',  -- [location_id, ...]
    redistributed_to    JSON DEFAULT '[]',  -- [{rep_id, location_ids[], new_date}, ...]
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
4.6 Существующие таблицы (без изменений)
routes — история LLM-оптимизаций (оставляем как есть)
metrics — метрики производительности моделей
optimization_results — сравнение до/после оптимизации
5. Новые / изменённые файлы бэкенда
5.1 Схема изменений
backend/src/
├── database/
│   ├── models.py                    ← ИЗМЕНИТЬ: добавить поля Location,
│   │                                            новые таблицы SalesRep,
│   │                                            VisitSchedule, VisitLog,
│   │                                            ForceMajeureEvent
│   └── migrations/
│       └── versions/
│           └── 002_add_reps_schedule.py  ← НОВЫЙ: миграция (чистая пересборка)
│
├── schemas/
│   ├── locations.py                 ← ИЗМЕНИТЬ: добавить category, city,
│   │                                            district, address
│   ├── reps.py                      ← НОВЫЙ: SalesRepCreate, SalesRepResponse,
│   │                                          SalesRepUpdate
│   ├── schedule.py                  ← НОВЫЙ: VisitScheduleItem, MonthlyPlan,
│   │                                          DailyRoute, GenerateScheduleRequest
│   └── force_majeure.py             ← НОВЫЙ: ForceMajeureRequest,
│                                             ForceMajeureResponse,
│                                             RedistributionResult
│
├── services/
│   ├── optimize.py                  ← ИЗМЕНИТЬ: убрать хардкод priority="A",
│   │                                            уважать категории в greedy (A→B→C→D)
│   ├── schedule_planner.py          ← НОВЫЙ: построение месячного плана
│   └── force_majeure_service.py     ← НОВЫЙ: логика перераспределения ТТ
│
└── routes/
    ├── reps.py                      ← НОВЫЙ: GET/POST/PATCH /reps
    ├── schedule.py                  ← НОВЫЙ: POST /schedule/generate,
    │                                          GET  /schedule,
    │                                          GET  /schedule/{rep_id}
    ├── force_majeure.py             ← НОВЫЙ: POST /force_majeure,
    │                                          GET  /force_majeure
    ├── visits.py                    ← НОВЫЙ: POST /visits,
    │                                          GET  /visits/stats
    ├── insights.py                  ← ИЗМЕНИТЬ: реальная аналитика
    └── locations.py                 ← ИЗМЕНИТЬ: парсить category при загрузке
5.2 Детали ключевых сервисов
services/schedule_planner.py — Алгоритм планировщика
SchedulePlanner.build_monthly_plan(
    locations: list[Location],   # все 250 ТТ с категориями
    reps: list[SalesRep],        # все активные сотрудники
    month: date,
    work_start: time = 09:00,
    work_end:   time = 18:00,
    days_per_week: int = 5
) → MonthlyPlan

Алгоритм:
1. Определить рабочие дни месяца (5 дней/нед, без праздников)
2. Для каждой ТТ по категории вычислить даты визитов:
   - A → 3 визита, равномерно: 1-я, 2-я, 3-я недели
   - B → 2 визита, равномерно: 1-я и 3-я недели
   - C → 1 визит, середина месяца
   - D → если текущий квартал совпадает → 1 визит, иначе skip
3. Собрать все пары (location_id, planned_date) → пул задач
4. Распределить пул по сотрудникам (round-robin с балансировкой):
   - MAX_TT_PER_DAY = floor(480 мин / (15 мин/ТТ + avg_travel))
   - Внутри дня одного сотрудника: greedy nearest-neighbor,
     сначала A-категория, затем B, C, D
5. Проверить: все ТТ попали в план нужное кол-во раз (100% охват)
6. Сохранить в visit_schedule (batch insert)
services/force_majeure_service.py — Алгоритм перераспределения
ForceMajeureService.handle(
    rep_id: str,
    event_date: date,
    fm_type: str,
    description: str
) → ForceMajeureResponse

Алгоритм:
1. Найти все visit_schedule: rep_id=X, date=event_date, status=planned
2. affected_tt_ids = [location_id из этих записей]
3. Если affected_tt_ids пуст → ничего не делать, записать событие
4. Найти активных сотрудников: status=active, id != rep_id
5. chunks = равномерно разбить affected_tt_ids на len(active_reps) частей
6. Для каждого сотрудника:
   - Найти ближайший рабочий день после event_date,
     когда count(planned_tt) < MAX_TT_PER_DAY
   - Создать новые visit_schedule записи (status=rescheduled)
7. Отменить старые записи (status=cancelled)
8. Если fm_type=illness → rep.status = sick
9. Сохранить ForceMajeureEvent с redistributed_to[]
routes/insights.py — Реальная аналитика (замена заглушки)
GET /api/v1/insights
→ {
    total_tt: 250,
    coverage_pct: float,              -- % ТТ с хотя бы 1 визитом в месяце
    visits_this_month: {
      planned: int,
      completed: int,
      completion_rate: float
    },
    by_category: {
      A: { total: 50, planned: N, completed: N, pct: float },
      B: { total: 75, ... },
      C: { total: 50, ... },
      D: { total: 75, ... }
    },
    by_district: [
      { district: "Саранск", total: 30, coverage_pct: float }, ...
    ],
    rep_activity: [
      { rep_id, rep_name, outings_count, tt_visited }, ...
    ],
    force_majeure_count: int          -- за текущий месяц
  }
6. Новые API-эндпоинты
Сотрудники
Метод	URL	Описание
GET	/api/v1/reps	Список всех сотрудников
POST	/api/v1/reps	Создать сотрудника (вручную через UI)
PATCH	/api/v1/reps/{rep_id}	Обновить статус/данные
DELETE	/api/v1/reps/{rep_id}	Удалить сотрудника
Планирование
Метод	URL	Описание
POST	/api/v1/schedule/generate	Сгенерировать план на месяц
GET	/api/v1/schedule?month=YYYY-MM	Полный план месяца
GET	/api/v1/schedule/{rep_id}?month=YYYY-MM	План конкретного сотрудника
GET	/api/v1/schedule/daily?date=YYYY-MM-DD	Маршруты всех сотрудников на день
Форс-мажоры
Метод	URL	Описание
POST	/api/v1/force_majeure	Зафиксировать инцидент + авторедистрибуция
GET	/api/v1/force_majeure?month=YYYY-MM	История инцидентов
Визиты
Метод	URL	Описание
POST	/api/v1/visits	Отметить фактический визит
GET	/api/v1/visits/stats?month=YYYY-MM	Статистика посещаемости
GET	/api/v1/visits?rep_id=&month=	История визитов с фильтрами
7. Генерация датасета 250 ТТ
Файл: scripts/generate_mordovia_dataset.py
Генерирует data/locations_mordovia_250.json по правилам организатора:

DISTRICTS = {
    "г.о. Саранск": {"count": 30, "lat": 54.1838, "lon": 45.1749, "radius_km": 8},
    "Ардатовский р-н":    {"count": 10, "lat": 54.8478, "lon": 46.2333, "radius_km": 3},
    "Атяшевский р-н":     {"count": 10, "lat": 54.5984, "lon": 46.0347, "radius_km": 3},
    # ... все 22 района с реальными координатами центров
}

CATEGORY_DISTRIBUTION = {
    "A": {"share": 0.20, "visits_per_month": 3, "time_window": ("09:00", "12:00")},
    "B": {"share": 0.30, "visits_per_month": 2, "time_window": ("09:00", "15:00")},
    "C": {"share": 0.20, "visits_per_month": 1, "time_window": ("09:00", "18:00")},
    "D": {"share": 0.30, "visits_per_quarter": 1, "time_window": ("09:00", "18:00")},
}
Для каждого района:

Категории распределяются по указанным долям (20/30/20/30)
Координаты генерируются случайно вокруг центра района (Gaussian noise)
Названия ТТ = типовые названия торговых точек Мордовии
Сохраняется в JSON + загружается через POST /api/v1/locations/upload
8. Обновления фронтенда
8.1 Типы (services/types.ts)
// Обновить существующий Location
interface Location {
  id: string
  name: string
  lat: number              // переименовать с latitude
  lon: number              // переименовать с longitude
  category: 'A' | 'B' | 'C' | 'D'   // НОВОЕ
  city: string             // НОВОЕ
  district: string         // НОВОЕ
  address: string
  time_window_start: string
  time_window_end: string
}

// Новые типы
interface SalesRep {
  id: string
  name: string
  status: 'active' | 'sick' | 'vacation' | 'unavailable'
  created_at: string
}

interface VisitScheduleItem {
  id: string
  location_id: string
  location_name: string
  location_category: 'A' | 'B' | 'C' | 'D'
  rep_id: string
  rep_name: string
  planned_date: string
  status: 'planned' | 'completed' | 'skipped' | 'rescheduled' | 'cancelled'
}

interface DailyRoute {
  rep_id: string
  rep_name: string
  date: string
  visits: VisitScheduleItem[]
  total_distance_km: number
  estimated_duration_hours: number
}

interface MonthlyPlan {
  month: string
  routes: DailyRoute[]
  total_tt_planned: number
  coverage_pct: number
}

interface ForceMajeureEvent {
  id: string
  type: 'illness' | 'weather' | 'vehicle_breakdown' | 'other'
  rep_id: string
  rep_name: string
  event_date: string
  description: string
  affected_tt_count: number
  redistributed_to: Array<{
    rep_id: string
    rep_name: string
    tt_count: number
    new_dates: string[]
  }>
}

interface Insights {
  total_tt: number
  coverage_pct: number
  visits_this_month: {
    planned: number
    completed: number
    completion_rate: number
  }
  by_category: Record<'A'|'B'|'C'|'D', {
    total: number
    planned: number
    completed: number
    pct: number
  }>
  by_district: Array<{
    district: string
    total: number
    coverage_pct: number
  }>
  rep_activity: Array<{
    rep_id: string
    rep_name: string
    outings_count: number
    tt_visited: number
  }>
  force_majeure_count: number
}
8.2 Новые страницы и компоненты
frontend/src/
├── views/
│   ├── ScheduleView.vue              ← НОВЫЙ
│   │   Календарь на месяц:
│   │   - Переключатель месяца
│   │   - Фильтр по сотруднику
│   │   - По дням: карточки маршрутов с ТТ и категориями
│   │   - Цветовая кодировка: A=красный, B=оранжевый, C=жёлтый, D=серый
│   │
│   ├── DashboardView.vue             ← ИЗМЕНИТЬ
│   │   Добавить карточки:
│   │   - % охвата ТТ (план/факт)
│   │   - Разбивка по категориям A/B/C/D
│   │   - Активные сотрудники / недоступные
│   │
│   └── AnalyticsView.vue             ← ИЗМЕНИТЬ
│       Добавить:
│       - График план vs факт по категориям (grouped bar)
│       - Воронка охвата по районам
│       - Таблица активности сотрудников
│
└── components/
    ├── reps/
    │   ├── RepsList.vue              ← НОВЫЙ
    │   │   Список сотрудников с статусами, кнопки добавить/изменить
    │   └── RepForm.vue               ← НОВЫЙ
    │       Форма создания/редактирования сотрудника
    │
    └── schedule/
        └── ForceMajeureModal.vue     ← НОВЫЙ
            Модальное окно форс-мажора:
            - Тип: Болезнь / Погодные условия / Неисправность ТС / Другое
            - Сотрудник (выбор из списка активных)
            - Дата инцидента
            - Описание
            - [Зафиксировать] → авторедистрибуция → показать результат
8.3 Навигация (router/index.ts)
// Добавить маршрут
{
  path: '/schedule',
  name: 'schedule',
  component: () => import('@/views/ScheduleView.vue')
}
9. Миграция БД
Стратегия
Полная пересборка (на основании решения: "Очистить и перезалить заново"):

Новая Alembic-миграция 002_add_reps_schedule.py
DROP + CREATE для таблиц с несовместимыми изменениями
ALTER TABLE для locations (добавить колонки)
После миграции → запустить scripts/generate_mordovia_dataset.py
10. Порядок реализации
#	Фаза	Что делаем	Ключевые файлы
1	БД	Новые таблицы + поля Location	models.py, миграция 002_
2	Схемы	Pydantic для новых сущностей	schemas/reps.py, schedule.py, force_majeure.py
3	Датасет	250 ТТ Мордовии с категориями	scripts/generate_mordovia_dataset.py
4	Сотрудники	CRUD API	routes/reps.py
5	Планировщик	Месячный план + API	services/schedule_planner.py, routes/schedule.py
6	Форс-мажор	Сервис + API	services/force_majeure_service.py, routes/force_majeure.py
7	Визиты	Логирование + статистика	routes/visits.py
8	Аналитика	Реальный /insights	routes/insights.py
9	Optimize fix	Убрать хардкод priority	services/optimize.py
10	Фронтенд	Типы → API → Views → UI	types.ts, api.ts, новые компоненты
11. Константы системы
# Категории и частота посещений
CATEGORY_VISIT_FREQUENCY = {
    "A": {"per_month": 3, "per_quarter": None},
    "B": {"per_month": 2, "per_quarter": None},
    "C": {"per_month": 1, "per_quarter": None},
    "D": {"per_month": None, "per_quarter": 1},
}

# Рабочий день
WORK_START_HOUR = 9
WORK_END_HOUR = 18
WORK_DAYS_PER_WEEK = 5
VISIT_DURATION_MIN = 15  # минут на одну ТТ

# Приоритет посещения внутри маршрута
CATEGORY_PRIORITY = {"A": 1, "B": 2, "C": 3, "D": 4}

# Распределение категорий
CATEGORY_DISTRIBUTION = {"A": 0.20, "B": 0.30, "C": 0.20, "D": 0.30}

# Скорость передвижения (км/ч)
URBAN_SPEED_KMH = 25
RURAL_SPEED_KMH = 40
Документ составлен на основе Excel-файла организатора (data/organizer_example.xlsx), PDF с функциональными требованиями, и технического анализа кодовой базы T2 Project.


---

Это полный план. Сохранить его как `PLAN.md` в корень проекта — дать команду, и создам файл в следующем шаге. Готов к реализации с Фазы 1 (миграция БД)?