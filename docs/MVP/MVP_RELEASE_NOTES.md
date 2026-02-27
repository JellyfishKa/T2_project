# Release Notes — T2

---

## v1.1.0 — Неделя 4 (27 февраля 2026)

**Тип:** Feature Release — Расписание, Трекинг времени, Excel

---

### Новые функции

#### Управление расписанием визитов

- **Алгоритм SchedulePlanner** — автоматическая генерация месячного плана с учётом категорий ТТ:
  - A: 3 визита/мес, B: 2 визита/мес, C: 1 визит/мес, D: 1 визит/квартал
  - Максимум 14 ТТ на ТП в день (рабочий день 09:00–18:00, Пн–Пт)
- **API расписания** (`POST /api/v1/schedule/generate`, `GET /api/v1/schedule/`, `PATCH /{id}/status`)
- **Трекинг времени** — `time_in`/`time_out` в ответах расписания через JOIN с VisitLog
- **Длительность визита** — чип ТТ показывает `(22м)` в UI

#### Торговые представители

- **CRUD API** (`GET/POST/PATCH/DELETE /api/v1/reps`)
- **Статусы** — active / sick / vacation / unavailable
- **RepsView** — новая страница управления сотрудниками

#### Форс-мажоры

- **Регистрация** — болезнь, отпуск, авария (`POST /api/v1/force_majeure`)
- **Автоперераспределение** — ForceMajeureService назначает визиты на доступных ТП
- **JSON журнал** — поле `redistributed_to` сохраняет маппинг визитов

#### LLM-варианты маршрута

- **3 варианта** на выбор через `POST /api/v1/optimize/variants`:
  - «По категориям» (приоритет A→B→C→D)
  - «Минимальное расстояние» (nearest-neighbor)
  - «Сбалансированный» (гибридный)
- **Pros/cons** от LLM для каждого варианта
- **Сохранение варианта** через `POST /api/v1/optimize/confirm`
- **Выбор модели** — Qwen 0.5B (быстрая) / Llama 1B (точнее) в Day modal

#### Excel интеграция

- **Экспорт** (`GET /api/v1/export/schedule?month=YYYY-MM`) — 4 листа:
  - Расписание — все плановые визиты
  - Журнал визитов — выполненные с длительностью (мин)
  - Статистика по ТТ — охват, % выполнения по категориям
  - Активность ТП — выходы на маршрут, % выполнения
- **Импорт** (`POST /api/v1/import/schedule`) — загрузка заполненного Excel:
  - Обновляет статусы VisitSchedule
  - Создаёт/обновляет VisitLog (time_in, time_out)
  - Возвращает `{updated, skipped, errors}`

#### Аналитика и инсайты

- **Реальные инсайты** (`GET /api/v1/insights?month=YYYY-MM`) — охват ТТ, % по категориям, активность ТП
- **Датасет 250 ТТ Мордовии** — 22 района + Саранск, реалистичные координаты
- **Исправление аналитики** — graceful degradation при недоступном `/benchmark/compare`

#### Новые страницы Frontend

- **ScheduleView** — месячный календарь с Day modal (LLM-оптимизация, список визитов с временами)
- **RepsView** — CRUD торговых представителей

---

### Исправления

- **Analytics crash fix** — `compareModels().catch(() => null)` предотвращает падение вкладки при 404
- **OptimizeView** — Qwen установлен моделью по умолчанию (быстрее, меньше RAM)

---

### CI/CD

- 182/182 frontend тестов (Vitest) — +3 новых мока в AnalyticsView.spec.ts
- 61/61 backend тестов (pytest)
- TypeScript: 0 ошибок

---

## v1.0.0 — MVP (25 февраля 2026)

**Тип:** MVP (Minimum Viable Product)

---

### Функции v1.0

#### Оптимизация маршрутов

- Единый endpoint `POST /api/v1/optimize` с автоматическим fallback (Qwen → Llama → Greedy)
- Прямой вызов: `/api/v1/qwen/optimize` и `/api/v1/llama/optimize`
- Временные окна, приоритеты, ограничения

#### Управление локациями

- `GET/POST /api/v1/locations/` — CRUD торговых точек
- `POST /api/v1/locations/upload` — загрузка из CSV/JSON
- Поля категоризации: category (A/B/C/D), city, district, address

#### История маршрутов

- `GET /api/v1/routes/` — список с пагинацией
- `GET /api/v1/routes/{id}` — детали с метриками

#### Метрики и аналитика

- `GET /api/v1/metrics` — время ответа, качество, стоимость по моделям
- `GET /api/v1/insights` — базовые рекомендации

#### Frontend (4 страницы)

- Home — лендинг с навигацией
- Dashboard — статистика маршрутов, метрики, сравнение моделей
- Optimize — форма ввода локаций, выбор модели, запуск оптимизации
- Analytics — графики, scatter plot, таблица статистики

#### Инфраструктура

- Docker Compose: backend, frontend, PostgreSQL, Redis
- Multi-stage Docker builds
- Nginx: проксирование API, SPA routing
- GitHub Actions CI/CD

---

### Системные требования

| Ресурс | Минимум | Рекомендация |
|--------|---------|--------------|
| RAM | 4 GB | 8 GB |
| Диск | 5 GB свободных | 10 GB |
| CPU | 2 ядра | 4 ядра |
| ОС | Ubuntu 22.04+ / Windows 10+ | Ubuntu 24.04 LTS |

---

### Известные ограничения

| # | Ограничение | Влияние |
|---|-------------|---------|
| 1 | Модели малого размера (Qwen 0.5B, Llama 1B) | Базовое качество оптимизации |
| 2 | Первый запрос к LLM — 5-15 сек (lazy loading) | Прогрев перед демо |
| 3 | CORS по умолчанию — только localhost | Для удалённого доступа — обновить allow_origins |
| 4 | Excel импорт — только лист «Расписание» | Другие листы игнорируются |

---

*См. также: [MVP_DEMO_CHECKLIST.md](MVP_DEMO_CHECKLIST.md) | [ARCHITECTURE.md](../ARCHITECTURE.md) | [API_CONTRACT.md](../API_CONTRACT.md)*
