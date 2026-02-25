# Руководство по сборке и запуску T2 на сервере

## Оглавление

1. [Текущее состояние проекта](#1-текущее-состояние-проекта)
2. [Что нужно на сервере](#2-что-нужно-на-сервере)
3. [Подготовка сервера](#3-подготовка-сервера)
4. [Клонирование и настройка проекта](#4-клонирование-и-настройка-проекта)
5. [Исправление docker-compose.yml](#5-исправление-docker-composeyml)
6. [Скачивание LLM моделей](#6-скачивание-llm-моделей)
7. [Запуск через Docker Compose](#7-запуск-через-docker-compose)
8. [Запуск без Docker (для отладки)](#8-запуск-без-docker-для-отладки)
9. [Проверка работоспособности](#9-проверка-работоспособности)
10. [Доступ через Tailscale](#10-доступ-через-tailscale)
11. [Нереализованные эндпоинты](#11-нереализованные-эндпоинты)
12. [Типичные проблемы и решения](#12-типичные-проблемы-и-решения)

---

## 1. Текущее состояние проекта

### Что ГОТОВО и работает

| Компонент | Статус | Описание |
|-----------|--------|----------|
| Frontend (Vue 3) | Готов | SPA с дашбордом, оптимизацией, аналитикой (4 страницы) |
| Backend (FastAPI) | Готов | 15 эндпоинтов: оптимизация, локации, маршруты, метрики, бенчмарки, insights |
| PostgreSQL | Готов | Схема, миграции, ORM модели |
| Redis | Готов | Контейнер настроен (кеширование) |
| Docker-файлы | Готовы | Multi-stage builds для backend и frontend |
| Nginx | Готов | Проксирование API, SPA routing |
| LLM клиенты | Готовы | QwenClient, LlamaClient (GGUF через llama-cpp) |
| CI/CD | Готов | GitHub Actions (тесты, линтинг, coverage) |

### Реализованные эндпоинты

| Эндпоинт | Что делает | Статус |
|----------|------------|--------|
| `GET /health` | Проверка здоровья системы | ✅ |
| `POST /api/v1/optimize` | Единый эндпоинт оптимизации (Qwen/Llama/auto) | ✅ |
| `POST /api/v1/qwen/optimize` | Прямой вызов Qwen | ✅ |
| `POST /api/v1/llama/optimize` | Прямой вызов Llama | ✅ |
| `GET /api/v1/locations/` | Список всех локаций | ✅ |
| `POST /api/v1/locations/` | Создание локации | ✅ |
| `GET /api/v1/metrics` | Метрики моделей | ✅ |
| `GET /api/v1/insights` | Рекомендации по выбору модели | ✅ |
| `POST /api/v1/benchmark/run` | Запуск бенчмарка | ✅ |
| `GET /api/v1/benchmark/compare` | Сравнение моделей | ✅ |
| `GET /api/v1/benchmark/status` | Статус бенчмарка | ✅ |
| `GET /api/v1/benchmark/latest` | Последний результат бенчмарка | ✅ |
| `GET /api/v1/routes/` | Список маршрутов (пагинация) | ✅ |
| `GET /api/v1/routes/{id}` | Детали маршрута с метриками | ✅ |
| `POST /api/v1/locations/upload` | Загрузка локаций из CSV/JSON файла | ✅ |

> **Вывод**: Все эндпоинты из API-контракта реализованы. Фронтенд полноценно работает на всех страницах.

---

## 2. Что нужно на сервере

### Минимальные требования

| Ресурс | Минимум | Рекомендация |
|--------|---------|--------------|
| RAM | 4 GB | 8 GB |
| Диск | 5 GB свободных | 10 GB |
| CPU | 2 ядра | 4 ядра |
| ОС | Ubuntu 22.04+ | Ubuntu 24.04 LTS |

> Ваш сервер: Ubuntu 24.04, ~55 GB диск — более чем достаточно.

### Необходимое ПО

- **Docker** + **Docker Compose plugin** (v2)
- **Git**
- **Python 3.11+** (для скачивания моделей)
- **pip** (для `huggingface-hub`)

---

## 3. Подготовка сервера

### 3.1 Подключение к серверу

```bash
ssh jellyfishka@100.120.184.98
```

### 3.2 Установка Docker (если ещё не установлен)

```bash
# Проверка — если docker уже есть, пропускай этот шаг
docker --version && docker compose version

# Если нет — устанавливаем
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Добавить себя в группу docker
sudo usermod -aG docker $USER
newgrp docker

# Проверка
docker run hello-world
```

### 3.3 Установка вспомогательных инструментов

```bash
sudo apt install -y python3 python3-pip python3-venv git htop
```

---

## 4. Клонирование и настройка проекта

### 4.1 Клонирование репозитория

```bash
cd ~
git clone git@github.com:JellyfishKa/T2_project.git
cd T2_project
```

> Если SSH-ключ для GitHub ещё не настроен — см. `docs/server-guide.md` раздел "Подключение GitHub через SSH".

### 4.2 Создание файла .env

```bash
cp .env.example .env
nano .env
```

Заполни значения:

```env
# Database
DATABASE_USER=postgres
DATABASE_PASSWORD=ПРИДУМАЙ_НАДЁЖНЫЙ_ПАРОЛЬ
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_NAME=t2

# LLM Models
QWEN_API_ENDPOINT=local
QWEN_MODEL_ID=qwen2-0_5b-instruct-q4_k_m.gguf
LLAMA_API_ENDPOINT=local
LLAMA_MODEL_ID=Llama-3.2-1B-Instruct-Q4_K_M.gguf

# Application
DEBUG=false
ENVIRONMENT=production
BACKEND_PORT=8000
FRONTEND_PORT=80
```

---

## 5. Исправление docker-compose.yml

### Проблема

Файл `docker-compose.yml` лежит в `backend/`, но пути сборки (`./backend`, `./frontend`) написаны так, как будто он в корне проекта. **Это не будет работать.**

### Решение: перенести docker-compose.yml в корень проекта

```bash
cd ~/T2_project
mv backend/docker-compose.yml ./docker-compose.yml
```

Теперь пути `./backend` и `./frontend` будут корректными относительно корня проекта.

### Альтернатива: если не хочешь двигать файл

Отредактируй `backend/docker-compose.yml` — замени пути:

```yaml
# Было:
  backend:
    build:
      context: ./backend
  # ...
    volumes:
      - ./backend/src/models:/app/src/models:ro
  frontend:
    build:
      context: ./frontend

# Стало:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
  # ...
    volumes:
      - ./src/models:/app/src/models:ro
  frontend:
    build:
      context: ../frontend
      dockerfile: Dockerfile
```

> **Рекомендация**: перенеси файл в корень — это стандартная практика и проще для понимания.

---

## 6. Скачивание LLM моделей

Модели нужно скачать **до запуска Docker**, потому что они монтируются как volume.

```bash
cd ~/T2_project

# Создать Python venv для скачивания
python3 -m venv .venv
source .venv/bin/activate
pip install huggingface-hub

# Скачать Qwen (~400 MB)
python3 -c "
from huggingface_hub import hf_hub_download
hf_hub_download(
    'Qwen/Qwen2-0.5B-Instruct-GGUF',
    'qwen2-0_5b-instruct-q4_k_m.gguf',
    local_dir='./backend/src/models/'
)
"

# Скачать Llama (~808 MB)
python3 -c "
from huggingface_hub import hf_hub_download
hf_hub_download(
    'bartowski/Llama-3.2-1B-Instruct-GGUF',
    'Llama-3.2-1B-Instruct-Q4_K_M.gguf',
    local_dir='./backend/src/models/'
)
"

# Проверка
ls -lh backend/src/models/*.gguf
# Ожидаем:
#   qwen2-0_5b-instruct-q4_k_m.gguf     (~400 MB)
#   Llama-3.2-1B-Instruct-Q4_K_M.gguf   (~808 MB)

deactivate
```

---

## 7. Запуск через Docker Compose

### 7.1 Сборка и запуск

```bash
cd ~/T2_project

# Убедись, что docker-compose.yml в корне (шаг 5)
# и .env файл создан (шаг 4.2)

# Сборка всех образов
docker compose build

# Запуск всех сервисов
docker compose up -d
```

### 7.2 Проверка статуса

```bash
# Все контейнеры должны быть в статусе "Up"
docker compose ps

# Ожидаемый вывод:
# NAME            STATUS                    PORTS
# t2_postgres     Up (healthy)              0.0.0.0:5432->5432/tcp
# t2_redis        Up                        0.0.0.0:6379->6379/tcp
# t2_backend      Up (health: starting)     0.0.0.0:8000->8000/tcp
# t2_frontend     Up                        0.0.0.0:80->80/tcp
```

### 7.3 Просмотр логов

```bash
# Все логи
docker compose logs -f

# Только backend (самое полезное при отладке)
docker compose logs -f backend

# Только frontend
docker compose logs -f frontend
```

### 7.4 Остановка

```bash
docker compose down          # Остановить, сохранить данные
docker compose down -v       # Остановить и удалить volumes (БД!)
```

---

## 8. Запуск без Docker (для отладки)

Если Docker-сборка падает или нужно быстро потестить бэкенд отдельно:

### 8.1 PostgreSQL и Redis через Docker

```bash
# Запустить только БД и кеш
docker compose up -d postgres redis
```

### 8.2 Backend вручную

```bash
cd ~/T2_project/backend

python3 -m venv venv
source venv/bin/activate
pip install -r requirements/prod/requirements.txt

# Указать переменные (localhost, т.к. БД работает через Docker)
export DATABASE_USER=postgres
export DATABASE_PASSWORD=ТВОЙ_ПАРОЛЬ
export DATABASE_HOST=localhost
export DATABASE_PORT=5432
export DATABASE_NAME=t2
export QWEN_MODEL_ID=qwen2-0_5b-instruct-q4_k_m.gguf
export LLAMA_MODEL_ID=Llama-3.2-1B-Instruct-Q4_K_M.gguf

# Запуск с hot-reload
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 8.3 Frontend вручную

```bash
cd ~/T2_project/frontend

# Нужен Node.js 20+
# Если нет — установи через nvm:
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc
nvm install 20
nvm use 20

npm install

# Указать URL бэкенда
export VITE_API_URL=http://localhost:8000/api/v1

npm run dev -- --host 0.0.0.0
# Фронт будет на порту 5173
```

---

## 9. Проверка работоспособности

### 9.1 Health check бэкенда

```bash
curl http://localhost:8000/health
```

Ожидаемый ответ:
```json
{
  "status": "ok",
  "database": "connected",
  "models": {
    "qwen": "not_loaded",
    "llama": "not_loaded"
  }
}
```

> `not_loaded` — нормально. Модели загрузятся при первом запросе (lazy loading).

### 9.2 Тест Qwen endpoint (единственный рабочий endpoint оптимизации)

```bash
curl -X POST http://localhost:8000/api/v1/qwen/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "locations": [
      {
        "ID": "loc_1",
        "name": "Красная площадь",
        "address": "Москва",
        "lat": 55.7539,
        "lon": 37.6208,
        "time_window_start": "10:00",
        "time_window_end": "22:00",
        "priority": "high"
      },
      {
        "ID": "loc_2",
        "name": "Парк Горького",
        "address": "Москва",
        "lat": 55.7298,
        "lon": 37.5995,
        "time_window_start": "08:00",
        "time_window_end": "23:00",
        "priority": "medium"
      }
    ],
    "constraints": {}
  }'
```

> Первый запрос займёт 5-15 секунд (загрузка модели в RAM). Последующие — быстрее.

### 9.3 Тест фронтенда

```bash
curl -s http://localhost:80 | head -5
# Должен вернуть HTML (index.html)
```

### 9.4 Swagger UI (интерактивная документация API)

Открой в браузере:
```
http://100.120.184.98:8000/docs
```

---

## 10. Доступ через Tailscale

### Порты и адреса

После запуска проект доступен через Tailscale по следующим адресам:

| Сервис | URL | Описание |
|--------|-----|----------|
| **Фронтенд** | `http://100.120.184.98` | Основной интерфейс (порт 80) |
| **Backend API** | `http://100.120.184.98:8000` | REST API |
| **Swagger UI** | `http://100.120.184.98:8000/docs` | Документация API |
| **PostgreSQL** | `100.120.184.98:5432` | БД (для подключения через DBeaver и т.д.) |

### CORS

Сейчас в `main.py` CORS разрешён только для `localhost:3000` и `localhost:5173`. Для доступа через Tailscale нужно добавить IP сервера.

**Временное решение** — в `backend/main.py` изменить:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Для разработки — разрешить все origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

> Или добавить конкретный origin: `"http://100.120.184.98"`.

### Nginx проксирование

Nginx в контейнере `t2_frontend` уже настроен проксировать `/api/*` на backend. Поэтому фронтенд на порту 80 может обращаться к API через свой же домен — это обходит проблему CORS для продакшн-сборки.

**Но** фронтенд в dev-режиме (порт 5173) обращается напрямую к `localhost:8000` — для этого CORS нужен.

---

## 11. Статус API-эндпоинтов

> **Обновлено 25.02.2026**: Все эндпоинты из API-контракта реализованы. Полный список — в разделе 1.

---

## 12. Типичные проблемы и решения

### Проблема: `docker compose build` падает на backend

**Причина**: `llama-cpp-python` требует компилятор C++.

**Решение**: Это уже обработано в Dockerfile (`gcc`, `build-essential`). Если всё равно падает — проверь логи:
```bash
docker compose build backend 2>&1 | tail -50
```

### Проблема: backend не может подключиться к PostgreSQL

**Причина**: `DATABASE_HOST` должен быть `postgres` (имя сервиса в Docker), не `localhost`.

**Решение**: В `.env` установи `DATABASE_HOST=postgres` для Docker, `localhost` для ручного запуска.

### Проблема: фронтенд показывает "Network Error"

**Причина**: CORS не разрешает запросы с IP сервера.

**Решение**: Добавить IP в `allow_origins` в `main.py` (см. раздел 10).

Или: используй фронтенд через порт 80 (Nginx) — он проксирует API и CORS не нужен.

### Проблема: `npm ci --only=production` в Dockerfile фронтенда

`--only=production` пропустит devDependencies (включая Vite, TypeScript). Сборка упадёт.

**Решение**: Заменить в `frontend/Dockerfile`:
```dockerfile
# Было:
RUN npm ci --only=production

# Стало:
RUN npm ci
```

### Проблема: GGUF модели не найдены в контейнере

**Причина**: Volume в docker-compose монтирует `./backend/src/models` — путь относительно docker-compose.yml.

**Решение**: Убедись, что docker-compose.yml перенесён в корень (шаг 5) и модели лежат в `backend/src/models/`.

### Проблема: порт 80 занят

```bash
# Проверка
sudo lsof -i :80

# Изменить порт фронтенда в docker-compose.yml:
ports:
  - "8080:80"   # Будет доступен на http://100.120.184.98:8080
```

---

## Чеклист запуска

- [ ] Подключиться к серверу через SSH
- [ ] Установить Docker (если нет)
- [ ] Клонировать репозиторий
- [ ] Создать `.env` файл
- [ ] Перенести `docker-compose.yml` в корень проекта
- [ ] Исправить `frontend/Dockerfile` (`npm ci` без `--only=production`)
- [ ] Скачать GGUF модели в `backend/src/models/`
- [ ] Добавить CORS для Tailscale IP (или `"*"` для разработки)
- [ ] `docker compose build`
- [ ] `docker compose up -d`
- [ ] Проверить `curl http://localhost:8000/health`
- [ ] Проверить `curl http://localhost:80`
- [ ] Открыть `http://100.120.184.98` в браузере
- [ ] Тестировать через Swagger UI: `http://100.120.184.98:8000/docs`
