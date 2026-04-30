# Руководство по развёртыванию T2 на сервере

**Версия:** v1.2.0 · **Обновлено:** 27.02.2026

---

## Оглавление

1. [Текущее состояние проекта](#1-текущее-состояние-проекта)
2. [Требования к серверу](#2-требования-к-серверу)
3. [Подготовка сервера](#3-подготовка-сервера)
4. [Клонирование и настройка](#4-клонирование-и-настройка)
5. [Скачивание LLM-моделей](#5-скачивание-llm-моделей)
6. [Запуск через Docker Compose](#6-запуск-через-docker-compose)
7. [Первоначальная загрузка данных](#7-первоначальная-загрузка-данных)
8. [Запуск без Docker (отладка)](#8-запуск-без-docker-отладка)
9. [Проверка работоспособности](#9-проверка-работоспособности)
10. [Доступ через Tailscale](#10-доступ-через-tailscale)
11. [Типичные проблемы и решения](#11-типичные-проблемы-и-решения)
12. [Чеклист развёртывания](#12-чеклист-развёртывания)

---

## 1. Текущее состояние проекта

### Что реализовано

| Компонент | Статус | Описание |
|-----------|--------|----------|
| Frontend (Vue 3 + TypeScript) | ✅ | 6 страниц: Home, Dashboard, Optimize, Analytics, Schedule, Reps |
| Backend (FastAPI + Python) | ✅ | 33 эндпоинта |
| PostgreSQL | ✅ | 8 таблиц: locations, sales_reps, visit_schedule, visit_log, force_majeure_events, routes, metrics, optimization_results |
| Redis | ✅ | Контейнер настроен (кеширование) |
| Docker Compose | ✅ | 4 сервиса: postgres, redis, backend, frontend |
| Nginx | ✅ | Проксирование `/api/*` → backend, SPA routing |
| Qwen 0.5B GGUF | ✅ | Оценка вариантов маршрута (pros/cons), lazy load |
| Llama 1B GGUF | ✅ | Альтернативная модель, lazy load |
| SchedulePlanner | ✅ | Алгоритм A/B/C/D, 14 ТТ/день, форс-мажоры, автоперенос skipped |
| Excel-экспорт | ✅ | 4 листа: Расписание, Журнал визитов, Статистика по ТТ, Активность ТП |
| 3 варианта оптимизации | ✅ | Greedy / Priority-first / Balanced + LLM evaluation |

### Полный список эндпоинтов

#### Система
| Эндпоинт | Описание |
|----------|----------|
| `GET /health` | Health check (DB + LLM статусы) |
| `GET /api/v1/health` | Health check для фронтенда |

#### Оптимизация маршрутов
| Эндпоинт | Описание |
|----------|----------|
| `POST /api/v1/optimize` | Greedy-оптимизация (< 100 мс) |
| `POST /api/v1/qwen/optimize` | Прямой вызов Qwen |
| `POST /api/v1/llama/optimize` | Прямой вызов Llama |
| `POST /api/v1/optimize/variants` | 3 варианта + LLM pros/cons (timeout 180 сек) |
| `POST /api/v1/optimize/confirm` | Сохранение выбранного варианта |

#### Торговые точки
| Эндпоинт | Описание |
|----------|----------|
| `GET /api/v1/locations/` | Список ТТ с пагинацией |
| `POST /api/v1/locations/` | Создание ТТ |
| `GET /api/v1/locations/{id}` | Детали ТТ |
| `PUT /api/v1/locations/{id}` | Обновление ТТ |
| `DELETE /api/v1/locations/{id}` | Удаление ТТ |
| `POST /api/v1/locations/upload` | Загрузка из XLSX/CSV/JSON |

#### Торговые представители
| Эндпоинт | Описание |
|----------|----------|
| `GET /api/v1/reps` | Список ТП |
| `POST /api/v1/reps` | Создание ТП |
| `PATCH /api/v1/reps/{id}` | Обновление |
| `DELETE /api/v1/reps/{id}` | Удаление |

#### Расписание и визиты
| Эндпоинт | Описание |
|----------|----------|
| `POST /api/v1/schedule/generate` | Генерация месячного плана |
| `GET /api/v1/schedule/` | Полный план на месяц |
| `GET /api/v1/schedule/daily` | Маршруты на конкретный день |
| `GET /api/v1/schedule/{rep_id}` | План конкретного ТП |
| `PATCH /api/v1/schedule/{id}` | Обновление статуса (skipped → автоперенос) |
| `POST /api/v1/force_majeure` | Форс-мажор + перераспределение |
| `GET /api/v1/force_majeure` | История форс-мажоров |
| `POST /api/v1/visits` | Фиксация визита |
| `GET /api/v1/visits/` | История визитов |
| `GET /api/v1/visits/stats` | Статистика посещаемости |

#### Аналитика и экспорт
| Эндпоинт | Описание |
|----------|----------|
| `GET /api/v1/metrics` | Метрики LLM |
| `GET /api/v1/insights` | Охват ТТ, активность ТП, районы |
| `GET /api/v1/routes/` | История маршрутов |
| `GET /api/v1/routes/{id}` | Детали маршрута |
| `GET /api/v1/export/schedule` | Excel-отчёт (4 листа) |
| `GET /api/v1/benchmark/compare` | Сравнение LLM-моделей |
| `GET /api/v1/benchmark/status` | Статус бенчмарка |
| `GET /api/v1/benchmark/latest` | Последний результат бенчмарка |

---

## 2. Требования к серверу

### Минимальные ресурсы

| Ресурс | Минимум | Рекомендация |
|--------|---------|--------------|
| RAM | 4 GB | **8 GB** (LLM требует ~1.2 GB под моделью) |
| Диск | 8 GB свободных | 15 GB (Qwen ~400 MB + Llama ~800 MB + образы ~3 GB) |
| CPU | 2 ядра | 4 ядра (inference быстрее) |
| ОС | Ubuntu 22.04+ | Ubuntu 24.04 LTS |

> **Ваш сервер:** `100.120.184.98` — Ubuntu 24.04, ~55 GB диск — достаточно.

### Необходимое ПО

- **Docker** + **Docker Compose plugin** (v2)
- **Git**
- **Python 3.11+** (только для скачивания моделей через huggingface-hub)

---

## 3. Подготовка сервера

### 3.1 Подключение

```bash
ssh jellyfishka@100.120.184.98
```

### 3.2 Установка Docker (если не установлен)

```bash
# Проверка
docker --version && docker compose version

# Установка (если нет)
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker

docker run hello-world   # Проверка
```

### 3.3 Вспомогательные инструменты

```bash
sudo apt install -y python3 python3-pip python3-venv git htop
```

---

## 4. Клонирование и настройка

### 4.1 Клонирование

```bash
cd ~
git clone git@github.com:JellyfishKa/T2_project.git
cd T2_project
```

> Если SSH-ключ ещё не добавлен — см. `docs/SERVER/server-guide.md`.

### 4.2 Создание `.env`

```bash
cp backend/.env.example backend/.env
nano backend/.env
```

Минимальная конфигурация:

```env
# Database
DATABASE_USER=postgres
DATABASE_PASSWORD=НАДЁЖНЫЙ_ПАРОЛЬ_ЗДЕСЬ
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_NAME=t2

# LLM Models
QWEN_MODEL_ID=qwen2-0_5b-instruct-q4_k_m.gguf
LLAMA_MODEL_ID=Llama-3.2-1B-Instruct-Q4_K_M.gguf

# Application
DEBUG=false
ENVIRONMENT=production
CORS_ORIGINS=http://100.120.184.98,http://localhost
```

> `DATABASE_HOST=postgres` — имя сервиса Docker, не `localhost`.

---

## 5. Скачивание LLM-моделей

Модели монтируются как Docker volume, их нужно скачать **до первого запуска**.

```bash
cd ~/T2_project

# Создать venv только для скачивания
python3 -m venv .venv_download
source .venv_download/bin/activate
pip install huggingface-hub

# Qwen 0.5B (~400 MB) — основная модель
python3 - <<'EOF'
from huggingface_hub import hf_hub_download
hf_hub_download(
    repo_id='Qwen/Qwen2-0.5B-Instruct-GGUF',
    filename='qwen2-0_5b-instruct-q4_k_m.gguf',
    local_dir='./backend/src/models/'
)
print("Qwen downloaded OK")
EOF

# Llama 1B (~808 MB) — альтернативная модель
python3 - <<'EOF'
from huggingface_hub import hf_hub_download
hf_hub_download(
    repo_id='bartowski/Llama-3.2-1B-Instruct-GGUF',
    filename='Llama-3.2-1B-Instruct-Q4_K_M.gguf',
    local_dir='./backend/src/models/'
)
print("Llama downloaded OK")
EOF

deactivate

# Проверка
ls -lh backend/src/models/*.gguf
# Ожидаем:
#   qwen2-0_5b-instruct-q4_k_m.gguf     ~400 MB
#   Llama-3.2-1B-Instruct-Q4_K_M.gguf   ~808 MB
```

---

## 6. Запуск через Docker Compose

### 6.1 Сборка и старт

```bash
cd ~/T2_project

# Убедиться: docker-compose.yml лежит в корне проекта
ls docker-compose.yml   # или backend/docker-compose.yml

# Если docker-compose.yml в backend/ — перенести в корень
mv backend/docker-compose.yml ./docker-compose.yml

# Сборка образов (занимает 5-15 минут при первом запуске)
docker compose build

# Запуск всех сервисов
docker compose up -d
```

### 6.2 Проверка статуса

```bash
docker compose ps
# NAME            STATUS               PORTS
# t2_postgres     Up (healthy)         0.0.0.0:5432->5432/tcp
# t2_redis        Up                   0.0.0.0:6379->6379/tcp
# t2_backend      Up (healthy)         0.0.0.0:8000->8000/tcp
# t2_frontend     Up                   0.0.0.0:80->80/tcp
```

### 6.3 Просмотр логов

```bash
docker compose logs -f          # все сервисы
docker compose logs -f backend  # только backend (наиболее информативно)
```

### 6.4 Остановка

```bash
docker compose down       # остановить, данные БД сохранятся
docker compose down -v    # остановить и удалить volumes (данные БД удалятся!)
```

### 6.5 Обновление после `git pull`

```bash
git pull
docker compose build backend  # пересобрать только backend (фронтенд если менялся тоже)
docker compose up -d
```

---

## 7. Первоначальная загрузка данных

После первого запуска база пустая. Нужно заполнить:

### 7.1 Загрузка торговых точек

```bash
# Через API (curl)
curl -X POST http://localhost:8000/api/v1/locations/upload \
  -F "file=@/путь/к/mordovia_tt.xlsx"

# Или через Swagger UI: http://localhost:8000/docs
# POST /api/v1/locations/upload
```

> Поддерживаемые форматы: `.xlsx`, `.csv`, `.json`
> Обязательные колонки: `name`, `lat`, `lon`, `time_window_start`, `time_window_end`
> Опциональные: `category` (A/B/C/D), `city`, `district`, `address`

### 7.2 Создание торговых представителей

```bash
curl -X POST http://localhost:8000/api/v1/reps \
  -H "Content-Type: application/json" \
  -d '{"name": "Иванов Иван Иванович"}'

# Повторить для каждого ТП (рекомендуется минимум 3)
```

### 7.3 Генерация месячного расписания

```bash
# Замените 2026-02 на текущий месяц
curl -X POST "http://localhost:8000/api/v1/schedule/generate" \
  -H "Content-Type: application/json" \
  -d '{"month": "2026-02"}'

# Ожидаемый ответ:
# {"month": "2026-02", "total_visits": 700, "coverage_pct": 85.0, ...}
```

---

## 8. Запуск без Docker (отладка)

### 8.1 Только БД и Redis через Docker

```bash
docker compose up -d postgres redis
```

### 8.2 Backend вручную

```bash
cd ~/T2_project/backend

python3 -m venv venv
source venv/bin/activate
pip install -r requirements/prod/requirements.txt

# Переменные окружения (localhost т.к. БД в Docker)
export DATABASE_USER=postgres
export DATABASE_PASSWORD=ВАШ_ПАРОЛЬ
export DATABASE_HOST=localhost
export DATABASE_PORT=5432
export DATABASE_NAME=t2
export QWEN_MODEL_ID=qwen2-0_5b-instruct-q4_k_m.gguf
export LLAMA_MODEL_ID=Llama-3.2-1B-Instruct-Q4_K_M.gguf

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 8.3 Frontend вручную

```bash
cd ~/T2_project/frontend

# Node.js 20+ (через nvm если нет)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc
nvm install 20 && nvm use 20

npm install
npm run dev -- --host 0.0.0.0
# Фронт будет на http://localhost:5173
```

---

## 9. Проверка работоспособности

### 9.1 Health check

```bash
curl http://localhost:8000/health
```

Ожидаемый ответ:

```json
{
  "status": "healthy",
  "database": "connected",
  "services": {
    "database": "connected",
    "qwen": "unavailable",
    "llama": "unavailable"
  }
}
```

> `"unavailable"` для моделей — нормально. Они загружаются лениво при первом запросе.

### 9.2 Тест оптимизации (быстрый greedy)

```bash
curl -X POST http://localhost:8000/api/v1/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "location_ids": ["ID_1", "ID_2", "ID_3"],
    "model": "auto"
  }'
# Ответ за < 1 секунды
```

### 9.3 Тест вариантов с LLM (долгий, 30-120 сек)

```bash
curl -X POST http://localhost:8000/api/v1/optimize/variants \
  -H "Content-Type: application/json" \
  -d '{
    "location_ids": ["ID_1", "ID_2", "ID_3"],
    "model": "qwen"
  }'
# Ожидать: 3 варианта с pros/cons
```

### 9.4 Тест экспорта Excel

```bash
curl -o test_export.xlsx \
  "http://localhost:8000/api/v1/export/schedule?month=2026-02"
ls -lh test_export.xlsx   # Должен быть > 5 KB
```

### 9.5 Тест фронтенда

```bash
curl -s http://localhost:80 | grep -o '<title>[^<]*</title>'
# Ожидаем: <title>T2 Logistics</title> или похожее
```

### 9.6 Swagger UI

```
http://100.120.184.98:8000/docs
```

---

## 10. Доступ через Tailscale

| Сервис | URL | Описание |
|--------|-----|----------|
| **Фронтенд** | `http://100.120.184.98` | Основной интерфейс |
| **Backend API** | `http://100.120.184.98:8000` | REST API |
| **Swagger UI** | `http://100.120.184.98:8000/docs` | Документация API |
| **PostgreSQL** | `100.120.184.98:5432` | БД (DBeaver, pgAdmin) |

### CORS настройка

В `.env` укажите:

```env
CORS_ORIGINS=http://100.120.184.98,http://localhost,http://localhost:5173
```

В `main.py` CORS настраивается автоматически из переменной `CORS_ORIGINS`.

> **Важно:** фронтенд через порт 80 (Nginx) проксирует API — CORS не нужен для продакшн.
> CORS нужен только при разработке (порт 5173 → порт 8000).

---

## 11. Типичные проблемы и решения

### Backend не стартует: `sqlalchemy connection refused`

**Причина:** PostgreSQL ещё не готов.

```bash
docker compose logs postgres | tail -20
# Ждать: "database system is ready to accept connections"
docker compose restart backend
```

### LLM зависает или SIGSEGV (exit 139)

**Причина:** Попытка загрузить Qwen и Llama одновременно — не хватает RAM.

**Решение:** Система корректно работает с одной моделью. В `/optimize/variants` выбирайте только **одну** модель (Qwen **или** Llama). Обе одновременно не загружаются.

### Analytics не загружается

**Причина:** Один из API-вызовов возвращает ошибку.

```bash
# Проверить вручную
curl http://localhost:8000/api/v1/insights?month=2026-02
curl http://localhost:8000/api/v1/benchmark/compare
curl "http://localhost:8000/api/v1/routes/?skip=0&limit=10"
```

Если данных нет (пустая БД) — загрузить ТТ, создать ТП, сгенерировать расписание (шаг 7).

### `npm ci --only=production` в Dockerfile фронтенда

**Причина:** `--only=production` пропускает devDependencies (Vite, TypeScript).

```dockerfile
# В frontend/Dockerfile заменить:
RUN npm ci --only=production
# На:
RUN npm ci
```

### GGUF модели не найдены

```bash
ls -lh backend/src/models/*.gguf
# Если нет — выполнить шаг 5 (скачивание моделей)
```

### Порт 80 занят

```bash
sudo lsof -i :80
# В docker-compose.yml изменить:
#   ports: ["8080:80"]
# Фронт будет на http://100.120.184.98:8080
```

### `docker compose build` падает на backend

```bash
# Посмотреть подробности
docker compose build backend 2>&1 | tail -50
# Обычно причина: отсутствует gcc/build-essential (уже в Dockerfile)
# Или: нет места на диске
df -h
```

---

## 12. Чеклист развёртывания

```
Подготовка:
  [ ] Подключиться к серверу (SSH)
  [ ] Установить Docker + Docker Compose
  [ ] Клонировать репозиторий

Настройка:
  [ ] Создать backend/.env из .env.example
  [ ] Убедиться что DATABASE_HOST=postgres (не localhost)
  [ ] Перенести docker-compose.yml в корень (если в backend/)
  [ ] Проверить frontend/Dockerfile — npm ci без --only=production

Модели:
  [ ] Скачать qwen2-0_5b-instruct-q4_k_m.gguf (~400 MB)
  [ ] Скачать Llama-3.2-1B-Instruct-Q4_K_M.gguf (~808 MB)
  [ ] ls -lh backend/src/models/*.gguf — оба файла присутствуют

Запуск:
  [ ] docker compose build
  [ ] docker compose up -d
  [ ] docker compose ps — все 4 контейнера Up
  [ ] curl http://localhost:8000/health → {"status": "healthy"}
  [ ] curl http://localhost:80 → HTML

Данные:
  [ ] Загрузить торговые точки (POST /locations/upload)
  [ ] Создать торговых представителей (POST /reps)
  [ ] Сгенерировать расписание (POST /schedule/generate)

Проверка функций:
  [ ] /optimize → маршрут за < 1 сек
  [ ] /optimize/variants → 3 варианта с метриками
  [ ] /export/schedule → Excel скачивается, 4 листа
  [ ] /schedule → отображается расписание
  [ ] /analytics → охват ТТ и активность ТП загружаются
```
