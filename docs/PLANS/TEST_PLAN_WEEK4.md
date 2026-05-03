# Тест-план — Неделя 4: Расписание, Трекинг визитов, Excel-интеграция, LLM-варианты

> **Версия**: 1.0
> **Дата**: 27 февраля 2026
> **Статус**: ✅ Все критерии приёмки выполнены

---

## 1. Введение

Тест-план недели 4 охватывает новый функционал:

| Модуль | Что тестируем |
|--------|--------------|
| Расписание визитов | Алгоритм SchedulePlanner, API `/schedule`, PATCH статуса |
| Трекинг времени | `time_in`/`time_out` в VisitLog, отображение длительности |
| Форс-мажоры | Регистрация события, перераспределение визитов |
| Excel экспорт | 4 листа: расписание, журнал, статистика, активность |
| Excel импорт | Загрузка заполненного файла, обновление БД |
| LLM варианты | `POST /optimize/variants` — 3 варианта + pros/cons |
| Сохранение варианта | `POST /optimize/confirm` → БД |
| Аналитика | Инсайты, сравнение моделей, fix crash |
| CI | Все 182 frontend-теста, 61 backend-тест |

---

## 2. Объём тестирования (Scope)

- **Backend**: pytest + pytest-asyncio, моки SQLAlchemy
- **Frontend**: Vitest + Vue Test Utils
- **Целевое покрытие**: Backend ≥ 64%, Frontend ≥ 70%
- **TypeScript**: `npx vue-tsc --noEmit` — 0 ошибок
- **CI**: GitHub Actions (все тесты проходят)

---

## 3. Тест-кейсы — Backend

### 3.1. API торговых представителей (`/reps`)

#### TC-REPS-001: Создание ТП
- **Метод**: `POST /api/v1/reps`
- **Вход**: `{"name": "Иванов А.А.", "status": "active"}`
- **Ожидаемый результат**: `201 Created`, тело содержит `id`, `name`, `status`

#### TC-REPS-002: Список ТП с фильтром
- **Метод**: `GET /api/v1/reps?status=active`
- **Ожидаемый результат**: `200 OK`, массив только активных ТП

#### TC-REPS-003: Обновление статуса
- **Метод**: `PATCH /api/v1/reps/{id}`
- **Вход**: `{"status": "sick"}`
- **Ожидаемый результат**: `200 OK`, `status` изменён; недопустимые значения → `422`

#### TC-REPS-004: Удаление ТП
- **Метод**: `DELETE /api/v1/reps/{id}`
- **Ожидаемый результат**: `204 No Content`; повторный GET → ТП недоступен (статус `unavailable`)

#### TC-REPS-005: Несуществующий ТП
- **Метод**: `PATCH /api/v1/reps/nonexistent-id`
- **Ожидаемый результат**: `404 Not Found`

---

### 3.2. Расписание визитов (`/schedule`)

#### TC-SCHED-001: Генерация расписания
- **Метод**: `POST /api/v1/schedule/generate`
- **Вход**: `{"month": "2026-02", "rep_ids": [...], "location_ids": [...]}`
- **Ожидаемый результат**: `200 OK`; создано ≥1 VisitSchedule; категория A получила 3 визита/мес

#### TC-SCHED-002: MAX_TT_PER_DAY
- **Описание**: Алгоритм не назначает более 14 ТТ одному ТП в один день
- **Проверка**: SQL запрос по `(planned_date, rep_id)` → `COUNT(*) ≤ 14`

#### TC-SCHED-003: Только рабочие дни
- **Описание**: Нет визитов в субботу (6) и воскресенье (7)
- **Проверка**: `planned_date.weekday() not in (5, 6)` для всех записей

#### TC-SCHED-004: Список расписания с фильтрами
- **Метод**: `GET /api/v1/schedule/?month=2026-02&rep_id={id}`
- **Ожидаемый результат**: Только записи указанного ТП за февраль

#### TC-SCHED-005: time_in/time_out в ответе
- **Описание**: Если VisitLog существует — `time_in` и `time_out` заполнены в ответе
- **Вход**: Создать VisitLog `schedule_id=X, time_in=10:00, time_out=10:22`
- **Запрос**: `GET /api/v1/schedule/?month=2026-02`
- **Ожидаемый результат**: Визит X содержит `"time_in": "10:00"`, `"time_out": "10:22"`

#### TC-SCHED-006: PATCH статуса → создание VisitLog
- **Метод**: `PATCH /api/v1/schedule/{id}/status`
- **Вход**: `{"status": "completed", "time_in": "10:00", "time_out": "10:30"}`
- **Ожидаемый результат**: `200 OK`; VisitLog создан с `time_in`, `time_out`

#### TC-SCHED-007: PATCH с неизвестным статусом
- **Вход**: `{"status": "flying"}`
- **Ожидаемый результат**: `422 Unprocessable Entity`

---

### 3.3. Форс-мажоры (`/force_majeure`)

#### TC-FM-001: Регистрация форс-мажора
- **Метод**: `POST /api/v1/force_majeure`
- **Вход**: `{"type": "illness", "rep_id": "...", "event_date": "2026-02-20"}`
- **Ожидаемый результат**: `201 Created`, событие сохранено в БД

#### TC-FM-002: Перераспределение визитов
- **Описание**: После регистрации болезни ТП его визиты переназначаются
- **Проверка**: `VisitSchedule.rep_id` обновлён на другого ТП; `redistributed_to` заполнен

#### TC-FM-003: Нет доступных ТП
- **Описание**: Все ТП статус `sick` — нет кому перераспределить
- **Ожидаемый результат**: Событие создано; `redistributed_to` пуст; предупреждение в ответе

#### TC-FM-004: Список форс-мажоров
- **Метод**: `GET /api/v1/force_majeure?month=2026-02`
- **Ожидаемый результат**: Массив событий только за февраль

---

### 3.4. Excel экспорт (`/export/schedule`)

#### TC-EXP-001: Успешный экспорт
- **Метод**: `GET /api/v1/export/schedule?month=2026-02`
- **Ожидаемый результат**: `200 OK`, `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

#### TC-EXP-002: Структура файла
- **Описание**: Excel содержит ровно 4 листа
- **Проверка**: `openpyxl.load_workbook(response.content).sheetnames == ["Расписание", "Журнал визитов", "Статистика по ТТ", "Активность ТП"]`

#### TC-EXP-003: Данные в листе «Расписание»
- **Описание**: Строка 3+ содержит плановые визиты; строка 2 — заголовок
- **Проверка**: `ws1.cell(2, 1).value == "Дата"`

#### TC-EXP-004: Длительность в журнале
- **Описание**: Если `time_in=10:00, time_out=10:30` → столбец «Длительность» = 30
- **Проверка**: `ws2.cell(row, 7).value == "30"`

#### TC-EXP-005: Неверный формат месяца
- **Метод**: `GET /api/v1/export/schedule?month=02-2026`
- **Ожидаемый результат**: `400 Bad Request`

---

### 3.5. Excel импорт (`/import/schedule`)

#### TC-IMP-001: Успешный импорт
- **Описание**: Загрузить корректный Excel с заполненными статусами
- **Метод**: `POST /api/v1/import/schedule` (multipart/form-data)
- **Ожидаемый результат**: `200 OK`; `updated > 0`; `skipped == 0`

#### TC-IMP-002: Создание VisitLog при импорте
- **Описание**: Строка со статусом «Выполнен» и временем → VisitLog создан в БД
- **Проверка**: `VisitLog.schedule_id = sched.id`, `time_in = "10:00"`, `time_out = "10:30"`

#### TC-IMP-003: Обновление существующего VisitLog
- **Описание**: VisitLog уже существует — поля `time_in`/`time_out` обновляются
- **Ожидаемый результат**: Без дублирования; старые значения перезаписаны

#### TC-IMP-004: Неизвестный сотрудник
- **Описание**: В Excel имя ТП не совпадает ни с одним `SalesRep.name`
- **Ожидаемый результат**: `skipped += 1`; в `errors`: `"Стр.X: сотрудник 'Неизвестный' не найден"`

#### TC-IMP-005: Неизвестная ТТ
- **Ожидаемый результат**: `skipped += 1`; ошибка в `errors`

#### TC-IMP-006: Неизвестный статус
- **Описание**: Статус «Отработан» (не в STATUS_MAP)
- **Ожидаемый результат**: `skipped += 1`; ошибка в `errors`

#### TC-IMP-007: Пустой файл / не Excel
- **Описание**: Загрузить `.txt` файл
- **Ожидаемый результат**: `400 Bad Request` с описанием ошибки

#### TC-IMP-008: Лимит ошибок в ответе
- **Описание**: 100 неверных строк → `errors` содержит не более 20
- **Проверка**: `len(response["errors"]) <= 20`

---

### 3.6. Оптимизация вариантов

#### TC-VAR-001: Генерация 3 вариантов
- **Метод**: `POST /api/v1/optimize/variants`
- **Вход**: `{"location_ids": ["id1", "id2", "id3", "id4"], "model": "qwen"}`
- **Ожидаемый результат**: `variants` массив длиной 3

#### TC-VAR-002: Структура варианта
- **Проверка**: Каждый вариант содержит `id`, `name`, `description`, `locations`, `metrics`, `pros`, `cons`

#### TC-VAR-003: Метрики варианта
- **Проверка**: `metrics.distance_km > 0`, `metrics.time_hours > 0`, `0 ≤ metrics.quality_score ≤ 100`

#### TC-VAR-004: Fallback при недоступной LLM
- **Описание**: LLM недоступна → `llm_evaluation_success=false`; варианты всё равно возвращаются
- **Ожидаемый результат**: `200 OK`; `pros`, `cons` пустые; `llm_evaluation_success=false`

#### TC-VAR-005: Менее 2 точек
- **Вход**: `{"location_ids": ["id1"]}`
- **Ожидаемый результат**: `422 Unprocessable Entity`

#### TC-VAR-006: Сохранение варианта
- **Метод**: `POST /api/v1/optimize/confirm`
- **Вход**: `{"name": "...", "locations": [...], "total_distance_km": 42.5, ...}`
- **Ожидаемый результат**: `200 OK`; маршрут сохранён в `routes` таблице

---

### 3.7. Инсайты и аналитика

#### TC-INS-001: Базовый инсайт
- **Метод**: `GET /api/v1/insights?month=2026-02`
- **Ожидаемый результат**: `total_tt`, `covered_tt`, `coverage_percent`, `category_stats`, `rep_activity`

#### TC-INS-002: coverage_percent корректен
- **Описание**: 50 выполненных из 100 ТТ → `coverage_percent = 50.0`

#### TC-INS-003: category_stats по всем категориям
- **Проверка**: Ключи `A`, `B`, `C`, `D` присутствуют в `category_stats`

#### TC-INS-004: Пустой месяц
- **Описание**: За месяц нет расписания → `coverage_percent=0`, пустые массивы

---

## 4. Тест-кейсы — Frontend (Vitest)

### 4.1. AnalyticsView.spec.ts

#### TC-FE-AN-001: Загрузка данных при монтировании
```typescript
expect(api.fetchRoutes).toHaveBeenCalledWith(0, 100)
expect(api.getMetrics).toHaveBeenCalled()
expect(api.compareModels).toHaveBeenCalled()
```

#### TC-FE-AN-002: Статистические карточки
```typescript
expect(wrapper.text()).toContain('Всего маршрутов')
expect(wrapper.text()).toContain('27.2 км')   // avg distance
expect(wrapper.text()).toContain('2500 ₽')    // avg cost
expect(wrapper.text()).toContain('86.0%')     // avg quality
```

#### TC-FE-AN-003: Отображение графиков (моки)
```typescript
expect(wrapper.findComponent({ name: 'BarChart' }).exists()).toBe(true)
expect(wrapper.findComponent({ name: 'ScatterChart' }).exists()).toBe(true)
expect(wrapper.findComponent({ name: 'LineChart' }).exists()).toBe(true)
```

#### TC-FE-AN-004: Ошибка загрузки
```typescript
vi.mocked(api.fetchRoutes).mockRejectedValue(new Error('Network error'))
// ...
expect(errorWrapper.text()).toContain('Ошибка загрузки данных')
```

#### TC-FE-AN-005: Кнопка «Обновить»
```typescript
const refreshButton = wrapper.findAll('button').find(b => b.text().includes('Обновить'))
await refreshButton?.trigger('click')
expect(api.fetchRoutes).toHaveBeenCalled()
```

#### TC-FE-AN-006: Пустые данные
```typescript
vi.mocked(api.fetchRoutes).mockResolvedValue({ total: 0, items: [] })
expect(emptyWrapper.text()).toContain('Нет данных для отображения')
```

#### TC-FE-AN-007: Форматирование моделей
```typescript
expect(vm.getModelName('llama')).toBe('Llama')
expect(vm.getModelName('qwen')).toBe('Qwen')
expect(vm.getModelName('unknown')).toBe('unknown')
```

#### TC-FE-AN-008: Scatter plot данные
```typescript
expect(scatterData.datasets[0].data).toHaveLength(3)
expect(scatterData.datasets[0].data[0]).toHaveProperty('x', 10.5)
```

#### TC-FE-AN-009: `getInsights` мокирован
- **Проверка**: `vi.mocked(api.getInsights)` не бросает «No export defined»
- **Результат**: Все 9 тестов AnalyticsView проходят

---

### 4.2. OptimizeView.spec.ts

#### TC-FE-OPT-001: Qwen как модель по умолчанию
```typescript
it('выбирает Qwen модель по умолчанию', async () => {
  expect(wrapper.find('input[value="qwen"]').element.checked).toBe(true)
  expect(wrapper.find('input[value="llama"]').element.checked).toBe(false)
})
```

#### TC-FE-OPT-002: Переключение модели
```typescript
await wrapper.find('input[value="llama"]').trigger('change')
expect(vm.selectedModel).toBe('llama')
```

---

### 4.3. ScheduleView (ручное тестирование)

| TC | Действие | Ожидаемый результат |
|----|----------|---------------------|
| TC-FE-SCH-001 | Открыть `/schedule` | Карточки маршрутов дня загружены |
| TC-FE-SCH-002 | Кликнуть «<» | Переход на предыдущий месяц |
| TC-FE-SCH-003 | Кликнуть на заголовок дня | Day modal открылся |
| TC-FE-SCH-004 | Выбрать Qwen → «Получить варианты» | 3 карточки вариантов появились |
| TC-FE-SCH-005 | Кликнуть на вариант | Border-синий выделен |
| TC-FE-SCH-006 | Нажать «Сохранить» | Modal закрыт; маршрут в `/routes` |
| TC-FE-SCH-007 | Кликнуть на чип визита | Модал с деталями ТТ открылся |
| TC-FE-SCH-008 | Выбрать «Выполнен» + время | time_in/time_out введены; PATCH отправлен |
| TC-FE-SCH-009 | Чип после save | Отображает `(22м)` длительность |
| TC-FE-SCH-010 | Нет LLM | Кнопка оптимизации → сообщение об ошибке |

---

### 4.4. Excel интеграция (ручное тестирование)

| TC | Действие | Ожидаемый результат |
|----|----------|---------------------|
| TC-EXCEL-001 | «Скачать Excel» (корректный месяц) | Файл `t2_schedule_YYYY-MM.xlsx` скачан |
| TC-EXCEL-002 | Открыть скачанный файл | 4 листа: Расписание, Журнал, Статистика, Активность |
| TC-EXCEL-003 | Заполнить статус «Выполнен» + время | — |
| TC-EXCEL-004 | «Загрузить Excel» заполненный файл | Блок «Импорт завершён: обновлено N» появился |
| TC-EXCEL-005 | Загрузить не-Excel файл | Ошибка «Не удалось прочитать Excel» |
| TC-EXCEL-006 | Загрузить с неизвестными именами | `errors` содержит список проблем |

---

## 5. Регрессионные тесты

#### TC-REG-001: Все frontend тесты
```bash
cd frontend && npx vitest run
# Ожидаемый результат: 182/182 passed
```

#### TC-REG-002: Все backend тесты
```bash
cd backend && pytest tests/ -v
# Ожидаемый результат: 61/61 passed
```

#### TC-REG-003: TypeScript type-check
```bash
cd frontend && npx vue-tsc --noEmit
# Ожидаемый результат: 0 ошибок
```

#### TC-REG-004: Health check
```bash
curl http://localhost:8000/health
# {"status": "healthy", "database": "connected", "services": {...}}
```

#### TC-REG-005: Оптимизация маршрута (smoke)
```bash
curl -X POST http://localhost:8000/api/v1/optimize \
  -H "Content-Type: application/json" \
  -d '{"location_ids": ["id1", "id2"], "model": "auto"}'
# {"model_used": "qwen"|"llama"|"greedy", ...}
```

---

## 6. Известные ограничения

| Ограничение | Описание |
|-------------|---------|
| Excel без openpyxl | При отсутствии `openpyxl` endpoint возвращает 500 (зависимость обязательна) |
| Импорт только «Расписание» | Другие листы Excel игнорируются при импорте |
| MAX ошибок в импорте | Возвращается не более 20 ошибок (длинный файл) |
| LLM время ответа | `optimizeVariants` может занять 5-15 сек при первом холодном старте модели |
| Категория D | Визиты D-категории планируются только если не превышен лимит дня |

---

## 7. Инструменты и среда

| Инструмент | Версия | Назначение |
|------------|--------|-----------|
| pytest | 7.x | Backend unit/integration тесты |
| pytest-asyncio | latest | Async endpoint тесты |
| Vitest | latest | Frontend unit тесты |
| Vue Test Utils | latest | Монтирование Vue-компонентов |
| openpyxl | 3.1+ | Проверка содержимого Excel |
| GitHub Actions | — | CI/CD (автозапуск тестов) |

---

## 8. Критерии приёмки недели 4

| Критерий | Статус |
|----------|--------|
| `time_in`/`time_out` в API расписания заполнены (JOIN с VisitLog) | ✅ |
| Day modal открывается по клику на день | ✅ |
| 3 варианта маршрута с pros/cons от LLM | ✅ |
| Выбор и сохранение варианта | ✅ |
| Excel экспорт (4 листа) | ✅ |
| Excel импорт с обновлением статусов и VisitLog | ✅ |
| Вкладка аналитики не падает (graceful compareModels) | ✅ |
| 182/182 frontend тестов проходят | ✅ |
| 61/61 backend тестов проходят | ✅ |
| TypeScript: 0 ошибок | ✅ |
| Конкурсное требование: «Отчёт о времени на каждой ТТ» | ✅ |
| Конкурсное требование: «Выгрузка аналитической информации» | ✅ |
