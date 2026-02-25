# Release Notes — T2 MVP 1.0

**Версия:** 1.0.0-mvp
**Дата релиза:** 25 февраля 2026
**Тип:** MVP (Minimum Viable Product)

---

## Обзор

T2 — AI-powered платформа оптимизации маршрутов розничной сети. MVP включает полный стек: backend на FastAPI, frontend на Vue 3, две LLM-модели (Qwen и Llama), PostgreSQL, Redis и Docker-инфраструктуру.

---

## Новые функции

### Оптимизация маршрутов
- **Единый эндпоинт оптимизации** (`POST /api/v1/optimize`) с автоматическим выбором модели и fallback-стратегией
- **Прямой вызов моделей** — Qwen (`/api/v1/qwen/optimize`) и Llama (`/api/v1/llama/optimize`)
- Поддержка временных окон, приоритетов и ограничений (вместимость, макс. расстояние)
- Автоматический fallback: если основная модель недоступна — переключение на резервную

### Управление локациями
- Создание локаций через API (`POST /api/v1/locations/`)
- Получение списка всех локаций (`GET /api/v1/locations/`)
- Загрузка локаций из CSV/JSON-файла (`POST /api/v1/locations/upload`)
- Хранение в PostgreSQL с ORM-моделями

### История маршрутов
- Список маршрутов с пагинацией (`GET /api/v1/routes/`)
- Детали маршрута с метриками (`GET /api/v1/routes/{id}`)

### Бенчмаркинг моделей
- Запуск бенчмарков (`POST /api/v1/benchmark/run`) с настраиваемым количеством итераций
- Сравнение моделей (`GET /api/v1/benchmark/compare`) — история результатов
- Статус выполнения (`GET /api/v1/benchmark/status`)
- Получение последнего результата (`GET /api/v1/benchmark/latest`)

### Метрики и аналитика
- Агрегированные метрики (`GET /api/v1/metrics`) — время ответа, качество, количество запусков
- Рекомендации по выбору модели (`GET /api/v1/insights`) на основе параметров задачи

### Frontend (Vue 3 + TypeScript)
- **Home** — лендинг с навигацией по разделам
- **Dashboard** — статистика маршрутов, метрики, сравнение моделей
- **Optimize** — форма ввода локаций, выбор модели, запуск оптимизации
- **Analytics** — графики производительности, scatter plot, таблица статистики
- Адаптивный дизайн (мобильные устройства, планшеты, десктоп)
- Skeleton-загрузчики, обработка ошибок, retry-логика

### Инфраструктура
- Docker Compose: backend, frontend, PostgreSQL, Redis
- Multi-stage Docker builds
- Nginx: проксирование API, SPA routing
- GitHub Actions CI/CD: тесты, линтинг, coverage
- Health check эндпоинт с проверкой БД и моделей

---

## Системные требования

| Ресурс | Минимум | Рекомендация |
|--------|---------|--------------|
| RAM | 4 GB | 8 GB |
| Диск | 5 GB свободных | 10 GB |
| CPU | 2 ядра | 4 ядра |
| ОС | Ubuntu 22.04+ / Windows 10+ | Ubuntu 24.04 LTS |
| Docker | Docker Engine 20+ | Docker Engine 24+ |
| Docker Compose | v2 | v2.20+ |

---

## Установка

Подробные инструкции — в [DEPLOYMENT_GUIDE.md](../SERVER/DEPLOYMENT_GUIDE.md).

Быстрый старт:

```bash
git clone git@github.com:JellyfishKa/T2_project.git
cd T2_project
cp .env.example .env
# Отредактировать .env (пароли, параметры)
# Скачать GGUF-модели в backend/src/models/
docker compose build
docker compose up -d
```

Проверка:
```bash
curl http://localhost:8000/health
# Фронтенд: http://localhost
# Swagger UI: http://localhost:8000/docs
```

---

## Известные ограничения

| # | Ограничение | Влияние |
|---|-------------|---------|
| 1 | Модели малого размера (Qwen 0.5B, Llama 1B) | Качество оптимизации — базовое; для продакшн нужны более крупные модели |
| 2 | Первый запрос к модели — 5-15 сек | Модели загружаются lazy; после прогрева — быстрее |
| 3 | CORS по умолчанию — только localhost | Для удалённого доступа нужно обновить `allow_origins` |

---

## Планы на следующий релиз (v1.1)

- [ ] Интеграция с более крупными LLM-моделями
- [ ] Кеширование результатов оптимизации в Redis
- [ ] Мониторинг (Prometheus + Grafana)
- [ ] Аутентификация и авторизация (JWT)
- [ ] Визуализация маршрутов на карте (Leaflet/Mapbox)
- [ ] Production-деплой с HTTPS

---

*См. также: [MVP_DEMO_CHECKLIST.md](MVP_DEMO_CHECKLIST.md) | [MVP_STAKEHOLDER_SUMMARY.md](MVP_STAKEHOLDER_SUMMARY.md) | [ARCHITECTURE.md](../ARCHITECTURE.md)*
