# MVP Demo Script — T2 AI Route Optimization

**Общая длительность:** ~15-20 минут
**Аудитория:** Stakeholders, Product Owner
**Формат:** Живая демонстрация + Swagger UI

---

## Подготовка окружения

```bash
# Убедиться что все сервисы запущены
docker compose up -d
docker compose ps

# Прогрев моделей (выполнить за 5 минут до демо)
curl -X POST http://localhost:8000/api/v1/qwen/optimize \
  -H "Content-Type: application/json" \
  -d '{"locations": [{"ID": "w1", "name": "Точка 1", "address": "Москва", "lat": 55.75, "lon": 37.62, "time_window_start": "09:00", "time_window_end": "18:00", "priority": "high"}, {"ID": "w2", "name": "Точка 2", "address": "Москва", "lat": 55.73, "lon": 37.60, "time_window_start": "09:00", "time_window_end": "18:00", "priority": "medium"}], "constraints": {}}'

curl -X POST http://localhost:8000/api/v1/llama/optimize \
  -H "Content-Type: application/json" \
  -d '{"locations": [{"ID": "w1", "name": "Точка 1", "address": "Москва", "lat": 55.75, "lon": 37.62, "time_window_start": "09:00", "time_window_end": "18:00", "priority": "high"}, {"ID": "w2", "name": "Точка 2", "address": "Москва", "lat": 55.73, "lon": 37.60, "time_window_start": "09:00", "time_window_end": "18:00", "priority": "medium"}], "constraints": {}}'
```

---

## Шаг 0.5: Загрузка тестовых данных (2 мин)

**Что показываем:** Автоматическая загрузка тестовых данных из файлов.

```bash
# Вариант 1: Bash-скрипт
bash scripts/seed_data.sh

# Вариант 2: Python-скрипт
python3 scripts/seed_data.py --host localhost --port 8000

# Вариант 3: Ручная загрузка CSV
curl -X POST http://localhost:8000/api/v1/locations/upload \
  -F "file=@data/locations_mordovia.csv"

# Вариант 4: Загрузка XLSX (файл организаторов)
curl -X POST http://localhost:8000/api/v1/locations/upload \
  -F "file=@data/organizer_example.xlsx"
```

**Говорим:**
> «Seed-скрипт автоматически загружает 30 торговых точек Мордовии, проверяет здоровье сервера и запускает тестовые оптимизации. Система поддерживает загрузку из CSV, JSON и XLSX файлов.»

**Доступные датасеты:**
- `data/locations_mordovia.csv` — 30 точек Мордовии (Саранск + районы)
- `data/locations_moscow.csv` — 15 точек Москвы
- `data/organizer_example.xlsx` — файл от организаторов

---

## Шаг 1: Проверка здоровья системы (2 мин)

**Что показываем:** Все компоненты запущены и работают.

```bash
curl http://localhost:8000/health | python -m json.tool
```

**Ожидаемый ответ:**
```json
{
  "status": "ok",
  "database": "connected",
  "models": {
    "qwen": "loaded",
    "llama": "loaded"
  }
}
```

**Говорим:**
> «Система состоит из 4 сервисов: backend на FastAPI, frontend на Vue 3, база данных PostgreSQL и Redis для кеширования. Все компоненты запускаются через Docker Compose одной командой. Health check показывает, что обе LLM-модели загружены и готовы к работе.»

---

## Шаг 2: Создание локаций через API (2 мин)

**Что показываем:** CRUD-операции с локациями магазинов.

```bash
# Создание локации
curl -X POST http://localhost:8000/api/v1/locations/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ТЦ Мега Химки",
    "latitude": 55.8970,
    "longitude": 37.3949,
    "address": "Химки, МКАД 65 км",
    "time_window_start": "10:00",
    "time_window_end": "22:00",
    "priority": 1
  }'

# Получение всех локаций
curl http://localhost:8000/api/v1/locations/ | python -m json.tool
```

**Говорим:**
> «Локации магазинов — это входные данные для оптимизации. Каждая локация содержит координаты, временные окна доставки и приоритет. Данные хранятся в PostgreSQL.»

---

## Шаг 3: Запуск оптимизации маршрута (3 мин)

**Что показываем:** Ключевая функция — AI-оптимизация маршрута.

### 3a. Через единый эндпоинт (авто-выбор модели)

Показать в **Swagger UI** (`http://localhost:8000/docs`) — эндпоинт `POST /api/v1/optimize`.

### 3b. Через прямой вызов Qwen

```bash
curl -X POST http://localhost:8000/api/v1/qwen/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "locations": [
      {"ID": "loc_1", "name": "Красная площадь", "address": "Москва, Кремль", "lat": 55.7539, "lon": 37.6208, "time_window_start": "10:00", "time_window_end": "22:00", "priority": "high"},
      {"ID": "loc_2", "name": "Парк Горького", "address": "Москва, Крымский вал", "lat": 55.7298, "lon": 37.5995, "time_window_start": "08:00", "time_window_end": "23:00", "priority": "medium"},
      {"ID": "loc_3", "name": "ВДНХ", "address": "Москва, пр-т Мира", "lat": 55.8264, "lon": 37.6377, "time_window_start": "09:00", "time_window_end": "21:00", "priority": "high"},
      {"ID": "loc_4", "name": "Москва-Сити", "address": "Москва, Пресненская наб.", "lat": 55.7494, "lon": 37.5392, "time_window_start": "08:00", "time_window_end": "20:00", "priority": "low"}
    ],
    "constraints": {}
  }'
```

**Говорим:**
> «Мы передаём 4 точки доставки с координатами и временными окнами. AI-модель Qwen анализирует данные и возвращает оптимальный порядок обхода, общее расстояние, время и стоимость. Модель работает локально на сервере — никакие данные не отправляются в облако.»

---

## Шаг 4: Просмотр истории маршрутов (2 мин)

**Что показываем:** API истории маршрутов и загрузка локаций из файла.

```bash
# Список маршрутов с пагинацией
curl "http://localhost:8000/api/v1/routes/?skip=0&limit=5" | python -m json.tool

# Детали конкретного маршрута (подставить ID из предыдущего ответа)
# curl http://localhost:8000/api/v1/routes/{route_id} | python -m json.tool
```

**Говорим:**
> «Все оптимизированные маршруты сохраняются в базу данных. Через API можно получить полный список с пагинацией и детали каждого маршрута с метриками модели.»

---

## Шаг 5: Просмотр Dashboard UI (3 мин)

**Что показываем:** Веб-интерфейс платформы.

1. Открыть `http://localhost` (или IP сервера)
2. Показать **Home** — обзор платформы и навигация
3. Перейти на **Dashboard** — статистика, метрики, список маршрутов
4. Перейти на **Optimize** — форма ввода локаций, выбор модели
5. Запустить оптимизацию через UI

**Говорим:**
> «Фронтенд предоставляет удобный интерфейс для работы с платформой. Dashboard показывает общую статистику и историю маршрутов. На странице Optimize можно ввести локации, выбрать модель и запустить оптимизацию в один клик.»

---

## Шаг 6: Запуск бенчмарка сравнения моделей (3 мин)

**Что показываем:** Сравнение производительности Qwen vs Llama.

```bash
# Запуск бенчмарка
curl -X POST "http://localhost:8000/api/v1/benchmark/run?iterations=3&use_mock=false"

# Проверка статуса
curl http://localhost:8000/api/v1/benchmark/status | python -m json.tool

# Получение результатов сравнения
curl http://localhost:8000/api/v1/benchmark/compare | python -m json.tool

# Последний результат
curl http://localhost:8000/api/v1/benchmark/latest | python -m json.tool
```

**Говорим:**
> «Система поддерживает бенчмаркинг — автоматическое сравнение моделей по скорости ответа, качеству оптимизации и надёжности. Это позволяет выбирать лучшую модель для конкретных сценариев.»

---

## Шаг 7: Просмотр метрик и аналитики (2 мин)

**Что показываем:** Аналитика и рекомендации по выбору модели.

```bash
# Метрики
curl http://localhost:8000/api/v1/metrics | python -m json.tool

# Рекомендации
curl "http://localhost:8000/api/v1/insights?num_locations=5" | python -m json.tool
```

Также показать страницу **Analytics** в UI:
- Графики производительности моделей
- Scatter plot: расстояние vs стоимость
- Таблица статистики по моделям

**Говорим:**
> «Аналитика агрегирует данные всех запусков и предоставляет рекомендации, какую модель использовать в зависимости от параметров задачи. Система учитывает количество локаций, ограничения по времени и историческую производительность моделей.»

---

## Завершение (2 мин)

**Ключевые тезисы для закрытия:**

1. **Полный стек** — Backend (15 API), Frontend (4 страницы), DB, LLM, Docker — всё работает как единое целое
2. **Два LLM** — Qwen (основная) и Llama (fallback) с автоматическим переключением
3. **Локальный запуск** — модели работают на сервере, данные не покидают инфраструктуру
4. **Аналитика** — бенчмаркинг, метрики, рекомендации по выбору модели
5. **Готовность к масштабированию** — Docker Compose, CI/CD, модульная архитектура

---

## Fallback-план

| Проблема | Решение |
|----------|---------|
| Backend не запускается | Показать Swagger UI на скриншотах; переключиться на `docker compose logs -f backend` для диагностики |
| LLM-модель не загружается | Использовать `use_mock=true` в бенчмарке; показать структуру ответа |
| Фронтенд не открывается | Демонстрировать через Swagger UI (`/docs`) — полностью интерактивная документация API |
| Медленный ответ модели | Объяснить: «Первый запрос загружает модель в RAM, последующие — быстрее»; использовать прогретую модель |
| CORS-ошибки в браузере | Использовать Swagger UI; или обращаться через Nginx (порт 80) |

---

## Тайминг

| Шаг | Действие | Длительность |
|-----|----------|-------------|
| 0 | Подготовка (до демо) | 5 мин |
| 0.5 | Загрузка тестовых данных | 2 мин |
| 1 | Health check | 2 мин |
| 2 | Создание локаций | 2 мин |
| 3 | Оптимизация маршрута | 3 мин |
| 4 | История маршрутов | 2 мин |
| 5 | Dashboard UI | 3 мин |
| 6 | Бенчмарк моделей | 3 мин |
| 7 | Метрики и аналитика | 2 мин |
| 8 | Завершение и вопросы | 5 мин |
| | **Итого** | **~22 мин** |

---

*См. также: [MVP_DEMO_CHECKLIST.md](MVP_DEMO_CHECKLIST.md) | [MVP_STAKEHOLDER_SUMMARY.md](MVP_STAKEHOLDER_SUMMARY.md) | [DEPLOYMENT_GUIDE.md](../SERVER/DEPLOYMENT_GUIDE.md)*
