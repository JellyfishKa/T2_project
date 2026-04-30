# T2 AI Route Planner — Проектная документация

**Конкурс:** «Внедрение ИИ-технологий для повышения эффективности работы розничной сети Т2»
**Версия:** v1.2.0
**Дата:** 27 февраля 2026
**Статус:** Production-Ready ✅

---

## Команда

| Имя | Роль | Зона ответственности |
|-----|------|----------------------|
| Сергей Маклаков | TL / PM | Архитектура, CI/CD, документация, координация |
| Роман Кижаев | Backend Engineer | FastAPI, SQLAlchemy, LLM-интеграция, Excel, алгоритмы |
| Владислав Наумкин | Frontend Engineer | Vue 3, TypeScript, UI/UX, прогресс-бар, 3 варианта маршрута |
| Дмитрий Мукасеев | ML / Analytics | SchedulePlanner, ForceMajeure, Insights API, датасет 250 ТТ |

**Период разработки:** 6 января — 27 февраля 2026 (4 недели)
**Методология:** Agile Lite (Kanban), 2-дневные итерации
**Репозиторий:** https://github.com/JellyfishKa/T2_project

---

## 1. Задача и требования конкурса

### 1.1 Контекст задачи

T2 поставила задачу разработать программу мониторинга и составления маршрутов торговой команды для сети из **250 торговых точек** в Мордовии (г.о. Саранск + 22 района).

### 1.2 Функциональные требования

**Блок 1 — Формирование оптимизированных маршрутов**

- Расчёт маршрутов с минимизацией километража
- Учёт рабочего времени торговых представителей (9:00–18:00, пн–пт)
- Сегментация ТТ по категориям A/B/C/D с учётом приоритетности посещения
- Гарантия 100% охвата базы ТТ, включая автоперенос пропущенных точек

**Блок 2 — Форс-мажоры**

- Анализ факторов: болезнь сотрудника, погодные условия, неисправность транспорта
- Автоматизированное перераспределение ТТ на других сотрудников
- Равномерное распределение по ближайшим доступным дням

**Блок 3 — Аналитика и выгрузка данных**

- Статистика по посещаемости торговых точек
- Отчёт о времени нахождения торгового представителя на каждой ТТ
- Детализация по времени и дате посещения каждой точки
- Учёт количества выходов торгового представителя на маршрут
- Выгрузка аналитической информации в Excel

### 1.3 Данные организатора

| Территория | ТТ | Категория | Частота |
|------------|-----|-----------|---------|
| г.о. Саранск | 50 | A (20%) | 3 раза/месяц |
| Ардатовский, Атяшевский, Атюрьевский р-ны | 30 | B (30%) | 2 раза/месяц |
| Дубёнский, Ельниковский, Зубово-Полянский р-ны | 20 | C (20%) | 1 раз/месяц |
| Инсарский, Ичалковский, Кадошкинский р-ны + ещё 9 районов | 75 | D (30%) | 1 раз/квартал |
| Остальные 12 районов | 75 | Смешанное | По категории |
| **ИТОГО** | **250 ТТ** | **4 категории** | **4 сотрудника** |

---

## 2. Решение и архитектура системы

### 2.1 Обзор решения

Создана полноценная веб-платформа **T2 AI Route Planner**, включающая:

- REST API бэкенд на FastAPI (Python 3.11)
- Vue 3 SPA фронтенд (6 страниц)
- PostgreSQL БД (8 таблиц)
- Два локальных LLM: Qwen 0.5B + Llama 1B (GGUF)
- Алгоритм SchedulePlanner (категории A/B/C/D, MAX 14 ТТ/день)
- Система форс-мажоров с round-robin перераспределением
- Excel-экспорт (4 листа) и обратный импорт
- Сравнение маршрутов до/после оптимизации через единый snapshot store
- CI/CD: GitHub Actions, 258+ тестов

Всё запускается в Docker Compose одной командой.

### 2.2 Высокоуровневая архитектура

```
┌──────────────────────────────────────────────────────────────────┐
│                       БРАУЗЕР (Vue 3 SPA)                        │
│   Home · Dashboard · Optimize · Analytics · Schedule · Reps      │
└───────────────────────────┬──────────────────────────────────────┘
                            │ HTTP (Nginx reverse proxy)
┌───────────────────────────▼──────────────────────────────────────┐
│               BACKEND FastAPI (Python 3.11)                       │
│  /optimize  /schedule  /reps  /force_majeure  /export  /visits    │
└──────┬──────────────┬─────────────────┬─────────────────────────┘
       │              │                 │
  ┌────▼────┐   ┌─────▼──────┐   ┌─────▼──────────────┐
  │PostgreSQL│  │   Redis    │   │   Qwen / Llama      │
  │ (8 табл) │  │  (кеш)    │   │   (GGUF/local)      │
  └──────────┘  └────────────┘   └────────────────────┘
```

### 2.3 Основные компоненты системы

| Компонент | Описание |
|-----------|----------|
| SchedulePlanner | Алгоритм построения месячного плана визитов (A×3, B×2, C×1, D×квартал) |
| Optimizer (3 варианта) | Greedy · Priority-first (A→D) · Balanced (60% dist + 40% prio) |
| ForceMajeureService | Round-robin перераспределение визитов при форс-мажоре |
| LLM: Qwen 0.5B | Генерация pros/cons для вариантов маршрута (GGUF, ~400 MB) |
| LLM: Llama 1B | Альтернативная модель по выбору пользователя (GGUF, ~808 MB) |
| Excel Export | 4 листа: Расписание / Журнал визитов / Статистика ТТ / Активность ТП |
| Insights API | Охват ТТ, план/факт, по категориям, по районам, активность сотрудников |
| Route Comparison | Snapshot до/после в `optimization_results`, shared modal в Dashboard и Analytics |

---

## 3. База данных

**PostgreSQL, 8 таблиц. ORM: SQLAlchemy 2.0 async. Миграции: Alembic.**

### locations — Торговые точки

| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID (PK) | Идентификатор |
| name | VARCHAR | Название ТТ |
| lat, lon | FLOAT | Координаты |
| category | ENUM | A / B / C / D |
| city | VARCHAR | Город |
| district | VARCHAR | Район |
| address | VARCHAR | Адрес |
| time_window_start / end | TIME | Окно посещения |

### sales_reps — Торговые представители

`id · name · status (active/sick/vacation/unavailable) · created_at`

### visit_schedule — Плановые визиты

`id · location_id (FK) · rep_id (FK) · planned_date · status (planned/completed/skipped/rescheduled/cancelled) · created_at`

### visit_log — Фактические визиты (трекинг времени)

`id · schedule_id (FK) · location_id (FK) · rep_id (FK) · visited_date · time_in · time_out · notes · created_at`

### force_majeure_events — Форс-мажоры

`id · type (illness/weather/vehicle_breakdown/other) · rep_id (FK) · event_date · description · affected_tt_ids (JSON) · redistributed_to (JSON) · created_at`

### routes — История LLM-маршрутов

`id · name · locations_order (JSON) · total_distance · total_time · total_cost · model_used · created_at`

### metrics — Метрики LLM

`id · route_id (FK) · model_name · response_time_ms · quality_score · cost · timestamp`

### optimization_results — Сравнение оптимизаций

`id · route_id (FK) · original_route (JSON) · optimized_route (JSON) · original_distance_km · original_time_hours · original_cost_rub · optimized_distance_km · optimized_time_hours · optimized_cost_rub · improvement_percentage · model_used · created_at`

---

## 4. Роадмап разработки (4 недели)

### Неделя 1 — Инфраструктура + LLM-интеграция
**6–13 января 2026 · Статус: ✅ Завершено**

- Инициализация репозитория, структура папок, CI/CD (GitHub Actions)
- FastAPI backend: базовые эндпоинты, SQLAlchemy async, PostgreSQL
- Интеграция LLM: QwenClient + LlamaClient (GGUF через llama-cpp-python)
- Vue 3 фронтенд: layout, роутинг, mock API
- ML: бенчмарк моделей, quality evaluator
- Docker Compose: 4 сервиса (postgres, redis, backend, frontend, nginx)
- **Результат:** базовая оптимизация маршрутов работает (`POST /optimize`)

**Роман:** FastAPI skeleton, DB init, QwenClient
**Владислав:** Vue 3 + Vite setup, Sidebar, mock HomeView
**Дмитрий:** LLM benchmark runner, quality evaluator
**Сергей:** Repo setup, CI/CD, Docker Compose, code review

---

### Неделя 2 — MVP — полная оптимизация
**14–21 января 2026 · Статус: ✅ Завершено**

- Единый `/optimize` endpoint с fallback (Qwen → Llama → Greedy)
- CRUD `/locations` с поддержкой CSV/JSON/XLSX загрузки
- Dashboard: статистика, метрики LLM, история маршрутов
- Analytics: графики Chart.js (расстояние, стоимость, качество)
- ML: сравнение Qwen vs Llama, benchmark runner
- Frontend: OptimizeView, DashboardView — полностью рабочие
- **Результат:** MVP feature-complete, все страницы работают

**Роман:** /optimize fallback, /locations CRUD, /routes, /metrics
**Владислав:** DashboardView, OptimizeView, AnalyticsView
**Дмитрий:** benchmark runner, /benchmark/compare, quality scoring
**Сергей:** API интеграция, code review, документация

---

### Неделя 3 — Production-Ready
**22–31 января 2026 · Статус: ✅ Завершено**

- Удалена T-Pro модель (16+ GB RAM, нестабильна)
- Финальная цепочка: Qwen → Greedy (Llama — по выбору, не одновременно)
- Docker multi-stage builds оптимизированы
- CI/CD: GitHub Actions, тесты, линтинг, coverage
- Nginx: SPA routing, API reverse proxy настроен
- **Результат:** стабильная production-ready система

**Роман:** /insights первая версия, hardening API
**Владислав:** prod builds, Nginx config, TypeScript strict
**Дмитрий:** mock LLM для тестов, benchmark CI
**Сергей:** Docker Compose prod config, server setup, Tailscale

---

### Неделя 4 — Расписание + Excel + Аналитика
**24–27 февраля 2026 · Статус: ✅ Завершено**

- БД: 4 новые таблицы (SalesRep, VisitSchedule, VisitLog, ForceMajeureEvent)
- SchedulePlanner: алгоритм A/B/C/D, MAX 14 ТТ/день, auto-reschedule skipped
- ForceMajeureService: round-robin перераспределение, 4 типа инцидентов
- LLM варианты: `/optimize/variants` (3 алгоритма + pros/cons от LLM)
- Excel export: 4 листа (Расписание, Журнал, Статистика, Активность ТП)
- Excel import: `POST /import/schedule` — обратная загрузка заполненного файла
- Analytics: реальный `/insights` API + UI с охватом ТТ по категориям
- ScheduleView + RepsView: новые страницы, Day modal, спиннер, кнопки
- CI: 182/182 frontend тестов, 61/61 backend тестов
- **Результат:** все конкурсные требования выполнены ✅

**Роман (BE-W4):** модели SalesRep/VisitSchedule/VisitLog/ForceMajeure, /reps CRUD, /schedule/generate, /force_majeure, /visits, /export/schedule, /optimize/variants + /confirm, /insights реальный
**Владислав (FE-W4):** ScheduleView (calendar + Day modal), RepsView CRUD, Excel кнопки, прогресс-бар вариантов, analytics fix (`compareModels().catch(()=>null)`)
**Дмитрий (ML-W4):** SchedulePlanner алгоритм, ForceMajeureService, generate_mordovia_dataset.py, datagen 250 ТТ
**Сергей (QA-W4):** 182 frontend тестов (Vitest), тест-план, документация (8 файлов)

---

## 5. Ключевые функции

### 5.1 ИИ-оптимизация маршрутов (3 варианта)

Система предлагает три детерминированных алгоритма. LLM используется для генерации pros/cons (оценки) каждого варианта.

| Вариант | Алгоритм | Логика |
|---------|----------|--------|
| 1 | Greedy (минимум расстояния) | Nearest-neighbor с матрицей расстояний Haversine. Минимизирует суммарный километраж. |
| 2 | Priority-first (A→B→C→D) | Сначала все точки A (greedy внутри группы), затем B, C, D. |
| 3 | Balanced (60% dist + 40% prio) | score = 0.6×distance + 0.4×priority_penalty. Компромисс. |

**Процесс:**
1. Вычисляются метрики 3 вариантов (расстояние, время, стоимость, quality_score)
2. LLM генерирует 2 pros и 2 cons для каждого варианта на русском языке
3. Graceful fallback: если LLM не ответила — варианты показываются с метриками без текста
4. Пользователь выбирает вариант → `POST /optimize/confirm` → сохранение в БД

### 5.2 Планировщик расписания (SchedulePlanner)

Алгоритм автоматически генерирует месячный план посещений для всей команды.

**Константы:**
- `WORK_START = 09:00` / `WORK_END = 18:00` (540 мин)
- `LUNCH_BREAK_MIN = 30`
- `VISIT_DURATION_MIN = 15`
- `AVG_TRAVEL_MIN_PER_TT = 20`
- `MAX_TT_PER_DAY = 14` = floor((540 − 30) / 35)

**Алгоритм (7 шагов):**
1. Определяет рабочие дни месяца (пн–пт, без выходных)
2. Для каждой ТТ по категории вычисляет плановые даты: A→нед.1,2,3; B→нед.1,3; C→середина; D→квартал
3. Собирает пул задач `(location_id, planned_date, category)`, сортирует по `(дата, приоритет)`
4. Round-robin распределение по сотрудникам с балансировкой загрузки
5. Ограничение: MAX 14 ТТ/день на сотрудника
6. Если ТТ помечена как `skipped` — автоматически создаётся новая запись на ближайший свободный день
7. Batch insert в `visit_schedule`, логирование `coverage_pct`

### 5.3 Форс-мажоры (ForceMajeureService)

Поддерживаются 4 типа инцидентов:

| Тип | Название | Поведение |
|-----|----------|-----------|
| `illness` | Болезнь | Перераспределение + меняет `rep.status → sick` |
| `weather` | Погодные условия | Только перераспределение ТТ |
| `vehicle_breakdown` | Неисправность транспорта | Только перераспределение ТТ |
| `other` | Другое | Произвольное описание |

**Алгоритм перераспределения:**
1. Находит все `planned` визиты сотрудника на дату инцидента
2. Получает список активных сотрудников (`status=active`, `id ≠ пострадавший`)
3. Делит ТТ равномерно методом `_chunked_round_robin()`
4. Для каждого сотрудника ищет ближайший рабочий день с `capacity < 14 ТТ`
5. Создаёт новые `visit_schedule` (`status=rescheduled`), отменяет старые (`cancelled`)
6. Записывает `ForceMajeureEvent` с `redistributed_to` JSON-полем

### 5.4 Excel-интеграция

**Экспорт (`GET /api/v1/export/schedule?month=YYYY-MM`):**

| Лист | Содержимое |
|------|------------|
| Расписание | Все плановые визиты с датами, сотрудниками, категориями ТТ, статусами |
| Журнал визитов | Выполненные визиты с `time_in`, `time_out`, длительностью в минутах |
| Статистика ТТ | Каждая ТТ: запланировано/выполнено/пропущено, % выполнения (условное форматирование) |
| Активность ТП | Каждый сотрудник: выходов на маршрут, ТТ посещено, % выполнения |

**Импорт (`POST /api/v1/import/schedule`):**
- Принимает multipart/form-data с заполненным xlsx
- Читает лист «Расписание» начиная со строки 3
- Матчит по паре `(date, rep_name, loc_name)`
- Обновляет `status` в `visit_schedule`, создаёт `VisitLog` при `status=completed`
- Возвращает `{updated, errors[:20]}` с описанием каждой проблемной строки

### 5.5 Трекинг времени на ТТ

- `VisitLog` хранит `time_in` / `time_out` (поля типа TIME)
- Создаётся при `status=completed` через `/visits` или Excel импорт
- GET `/schedule/` возвращает `time_in` / `time_out` в формате `"HH:MM"` через JOIN
- Excel «Журнал визитов»: длительность = `time_out − time_in` в минутах

### 5.6 Сравнение маршрутов до и после оптимизации

- После сохранения маршрута `POST /api/v1/optimize/confirm` в `optimization_results` фиксируются не только `original_route` и `optimized_route`, но и обе группы snapshot-метрик: расстояние, время и стоимость до и после оптимизации.
- `GET /api/v1/routes` и `GET /api/v1/routes/{id}` отдают флаг `has_comparison`, поэтому UI не показывает compare action для legacy-маршрутов без полного snapshot.
- `GET /api/v1/routes/{id}/comparison` возвращает две упорядоченные последовательности точек с координатами и блок `diff`: `distance_delta_km`, `time_delta_hours`, `cost_delta_rub`, `changed_stops_count`, `improvement_percentage`.
- В Dashboard и Analytics используется общая `RouteCompareModal`: на одной карте поверх друг друга отображаются две полилинии, а справа пользователь видит перестановки точек и краткое summary.
- Практическая ценность для демо: можно не только показать итоговую оптимизацию, но и объяснить, за счёт каких перестановок получена экономия по километражу, времени и стоимости.

---

## 6. Полный список API-эндпоинтов

**Итого: 33 эндпоинта**

### Система

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/health` | Health check (DB + LLM статусы) |
| GET | `/api/v1/health` | Health check для фронтенда |

### Оптимизация маршрутов

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/v1/optimize` | Greedy-оптимизация (< 100 мс) |
| POST | `/api/v1/qwen/optimize` | Прямой вызов Qwen |
| POST | `/api/v1/llama/optimize` | Прямой вызов Llama |
| POST | `/api/v1/optimize/variants` | 3 варианта + LLM pros/cons (timeout 180 сек) |
| POST | `/api/v1/optimize/confirm` | Сохранение выбранного варианта |

### Торговые точки

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/v1/locations/` | Список ТТ с пагинацией |
| POST | `/api/v1/locations/` | Создание ТТ |
| GET | `/api/v1/locations/{id}` | Детали ТТ |
| PUT | `/api/v1/locations/{id}` | Обновление ТТ |
| DELETE | `/api/v1/locations/{id}` | Удаление ТТ |
| POST | `/api/v1/locations/upload` | Загрузка из XLSX/CSV/JSON |

### Торговые представители

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/v1/reps` | Список ТП |
| POST | `/api/v1/reps` | Создание ТП |
| PATCH | `/api/v1/reps/{id}` | Обновление (статус, имя) |
| DELETE | `/api/v1/reps/{id}` | Удаление ТП |

### Расписание

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/v1/schedule/generate` | Генерация месячного плана |
| GET | `/api/v1/schedule/` | Полный план на месяц |
| GET | `/api/v1/schedule/daily` | Маршруты всех ТП на конкретный день |
| GET | `/api/v1/schedule/{rep_id}` | План конкретного ТП |
| PATCH | `/api/v1/schedule/{id}` | Обновление статуса (skipped → автоперенос) |

### Форс-мажоры и визиты

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/v1/force_majeure` | Форс-мажор + перераспределение ТТ |
| GET | `/api/v1/force_majeure` | История форс-мажоров |
| POST | `/api/v1/visits` | Фиксация визита (time_in/time_out) |
| GET | `/api/v1/visits/` | История визитов с фильтрами |
| GET | `/api/v1/visits/stats` | Статистика посещаемости за месяц |

### Аналитика и экспорт

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/v1/metrics` | Метрики LLM-моделей |
| GET | `/api/v1/insights` | Охват ТТ, активность ТП, по районам |
| GET | `/api/v1/routes/` | История маршрутов (пагинация) |
| GET | `/api/v1/routes/{id}` | Детали маршрута с метриками |
| GET | `/api/v1/routes/{id}/comparison` | Snapshot-сравнение маршрута до/после |
| GET | `/api/v1/export/schedule` | Excel-отчёт 4 листа (`?month=YYYY-MM`) |
| GET | `/api/v1/benchmark/compare` | Сравнение LLM-моделей |

---

## 7. Технологический стек

### Backend

| Параметр | Значение |
|----------|----------|
| Язык | Python 3.11+ |
| Фреймворк | FastAPI (async, Pydantic v2) |
| ORM | SQLAlchemy 2.0 (async) + Alembic |
| База данных | PostgreSQL 15 + asyncpg |
| Кеш | Redis 7 |
| LLM Runtime | llama-cpp-python 0.3.16 (GGUF) |
| Модель 1 | Qwen2-0.5B-Instruct Q4_K_M (~400 MB, ~0.6 GB RAM) |
| Модель 2 | Llama-3.2-1B-Instruct Q4_K_M (~808 MB, ~1.2 GB RAM) |
| Excel | openpyxl 3.1.5 (чтение + запись) |
| Тестирование | pytest + pytest-asyncio (61 тест, 64% coverage) |

### Frontend

| Параметр | Значение |
|----------|----------|
| Фреймворк | Vue 3 + Vite 5 + TypeScript |
| Стилизация | TailwindCSS 3 |
| Графики | Chart.js 4 + vue-chartjs |
| HTTP | Axios (с retry + timeout) |
| Тестирование | Vitest + Vue Test Utils (182 теста, ~70% coverage) |
| Страницы | Home · Dashboard · Optimize · Analytics · Schedule · Reps |

### DevOps & Infrastructure

| Параметр | Значение |
|----------|----------|
| Контейнеры | Docker + Docker Compose (4 сервиса) |
| Реверс-прокси | Nginx (SPA routing + API proxy) |
| CI/CD | GitHub Actions (lint + test + coverage) |
| Сервер | Ubuntu 24.04, ~55 GB disk, Tailscale VPN |
| Адреса | `http://100.120.184.98` (фронт) · `:8000` (API) · `:8000/docs` (Swagger) |

### Требования к серверу

| Ресурс | Минимум | Рекомендуется |
|--------|---------|---------------|
| RAM | 4 GB | 8 GB (LLM занимает ~1.2 GB) |
| Диск | 8 GB | 15 GB (модели + образы Docker) |
| CPU | 2 ядра | 4 ядра (inference быстрее) |
| ОС | Ubuntu 22.04+ | Ubuntu 24.04 LTS |

---

## 8. Тестирование и качество

### Покрытие

| Компонент | Тестов | Coverage | Команда |
|-----------|--------|----------|---------|
| Backend (pytest) | 61 | 64% | `pytest tests/ -v --cov=src` |
| Frontend (vitest) | 182 | ~70% | `npx vitest run --coverage` |
| ML/Benchmarks | 15 | ~80% | `python ml/benchmarks/llm_benchmark.py --mock` |
| TypeScript | 0 ошибок | 100% | `npx tsc --noEmit` |
| **ИТОГО** | **258+** | **~68%** | GitHub Actions (CI) |

### Ключевые тест-кейсы

- `POST /optimize` — возвращает упорядоченный список `location_ids` за < 1 сек
- `POST /optimize/variants` — возвращает ровно 3 варианта с метриками
- `POST /schedule/generate` — все ТТ получают нужное кол-во визитов по категории
- `PATCH /schedule/{id}` status=skipped — автоматически создаётся `rescheduled` запись
- `POST /force_majeure` — все `affected_tt_ids` перераспределяются, ни одна не теряется
- `GET /export/schedule` — Excel файл содержит 4 листа, размер > 5 KB
- `GET /insights` — `coverage_pct` корректно считается от реальных ТТ в БД

### Производительность

| Операция | Время | Примечание |
|----------|-------|------------|
| `POST /optimize` | < 100 мс | Greedy nearest-neighbor, чистый Python |
| `POST /optimize/variants` | 30–90 сек | Включает LLM inference для pros/cons |
| `POST /schedule/generate` | < 500 мс | 250 ТТ, 4 сотрудника, 1 месяц |
| `GET /export/schedule` | < 2 сек | openpyxl генерация 4 листов |
| `POST /force_majeure` | < 200 мс | БД-операции, без LLM |
| LLM: первый запрос | 5–15 сек | Загрузка GGUF модели в RAM |
| LLM: последующие запросы | 3–8 сек | Модель уже в памяти (lazy load) |

---

## 9. Развёртывание

### Быстрый старт (Docker Compose)

```bash
# 1. Клонировать репозиторий
git clone https://github.com/JellyfishKa/T2_project.git
cd T2_project

# 2. Создать .env
cp backend/.env.example backend/.env
# Заполнить DATABASE_PASSWORD

# 3. Скачать LLM модели (~1.2 GB суммарно)
python3 -m venv .venv_download && source .venv_download/bin/activate
pip install huggingface-hub
python3 -c "
from huggingface_hub import hf_hub_download
hf_hub_download('Qwen/Qwen2-0.5B-Instruct-GGUF',
    'qwen2-0_5b-instruct-q4_k_m.gguf', local_dir='backend/src/models/')
hf_hub_download('bartowski/Llama-3.2-1B-Instruct-GGUF',
    'Llama-3.2-1B-Instruct-Q4_K_M.gguf', local_dir='backend/src/models/')
"

# 4. Собрать и запустить
docker compose build
docker compose up -d

# 5. Проверить
curl http://localhost:8000/health  # {"status": "healthy"}

# 6. Загрузить данные
curl -X POST http://localhost:8000/api/v1/locations/upload -F "file=@mordovia_250.xlsx"
curl -X POST http://localhost:8000/api/v1/reps -H "Content-Type: application/json" \
     -d '{"name": "Иванов Иван Иванович"}'
curl -X POST "http://localhost:8000/api/v1/schedule/generate" \
     -H "Content-Type: application/json" -d '{"month": "2026-02"}'
```

### Адреса сервисов

| Сервис | URL |
|--------|-----|
| Фронтенд | http://100.120.184.98 |
| Backend API | http://100.120.184.98:8000 |
| Swagger UI | http://100.120.184.98:8000/docs |
| PostgreSQL | 100.120.184.98:5432 |

### Переменные окружения (.env)

| Переменная | Пример | Описание |
|------------|--------|----------|
| `DATABASE_USER` | `postgres` | Пользователь PostgreSQL |
| `DATABASE_PASSWORD` | `СЕКРЕТ` | Обязательно изменить! |
| `DATABASE_HOST` | `postgres` | Имя Docker сервиса (не localhost) |
| `DATABASE_NAME` | `t2` | Имя базы данных |
| `QWEN_MODEL_ID` | `qwen2-0_5b-instruct-q4_k_m.gguf` | Имя файла модели |
| `LLAMA_MODEL_ID` | `Llama-3.2-1B-Instruct-Q4_K_M.gguf` | Имя файла модели |
| `CORS_ORIGINS` | `http://100.120.184.98,...` | Разрешённые origins |

---

## 10. Соответствие конкурсным требованиям

### Блок 1 — Оптимизация маршрутов

| # | Требование | Статус | Реализация |
|---|------------|--------|------------|
| 1.1 | Расчёт маршрутов с минимизацией километража | ✅ Выполнено | Greedy (Haversine + nearest-neighbor). `/optimize` + `/optimize/variants`. 15–20% экономия. |
| 1.2 | Учёт рабочего времени торговых представителей | ✅ Выполнено | SchedulePlanner: 09:00–18:00, пн–пт, MAX 14 ТТ/день. |
| 1.3 | Сегментация ТТ по категориям A/B/C/D | ✅ Выполнено | A=3x/мес, B=2x, C=1x, D=квартал. Priority-first алгоритм. Цвет в UI. |
| 1.4 | 100% охват базы ТТ + механизм пропущенных точек | ✅ Выполнено | `coverage_pct` в `/insights`. `skipped` → автоматически создаётся `rescheduled`. |

### Блок 2 — Форс-мажоры

| # | Требование | Статус | Реализация |
|---|------------|--------|------------|
| 2.1 | Анализ факторов форс-мажора | ✅ Выполнено | 4 типа: illness, weather, vehicle_breakdown, other. `force_majeure_events` таблица. |
| 2.2 | Автоматическое перераспределение ТТ | ✅ Выполнено | Round-robin по активным ТП, поиск ближайшего дня с capacity < 14. |
| 2.3 | Равномерное распределение на ближайшие дни | ✅ Выполнено | `_chunked_round_robin()` + `_find_available_day()` до 30 дней вперёд. |

### Блок 3 — Аналитика и выгрузка данных

| # | Требование | Статус | Реализация |
|---|------------|--------|------------|
| 3.1 | Статистика по посещаемости ТТ | ✅ Выполнено | `/visits/stats` + `/insights`: план/факт, по категориям, по районам, `coverage_pct`. |
| 3.2 | Отчёт о времени нахождения ТП на каждой ТТ | ✅ Выполнено | `time_in`/`time_out` в `VisitLog`. Excel «Журнал визитов» с длительностью в минутах. |
| 3.3 | Детализация по времени и дате посещения | ✅ Выполнено | `VisitLog`: `visited_date` + `time_in` + `time_out`. API `/visits` + Excel лист 2. |
| 3.4 | Количество выходов ТП на маршрут | ✅ Выполнено | `outings_count` в `/insights` (уникальные дни с визитами). Excel «Активность ТП». |
| 3.5 | Выгрузка аналитической информации | ✅ Выполнено | `GET /export/schedule?month=YYYY-MM` → Excel 4 листа. Одна кнопка в UI. |

---

> **Итог: все 12 конкурсных требований выполнены.**
>
> Платформа реализует полный цикл: загрузка данных → планирование → трекинг → аналитика → экспорт.
> Локальный ИИ: данные клиентов не покидают сервер компании.
> **33 API эндпоинта · 8 таблиц БД · 6 страниц UI · 258+ тестов**

---

*Команда T2 · Мордовия · Февраль 2026*
