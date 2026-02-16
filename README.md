# T2 Розничная сеть

**AI-powered оптимизация маршрутов и сетевая аналитика для розничной торговли**

## Описание проекта

T2 Розничная сеть — это комплексная платформа на основе искусственного интеллекта для оптимизации маршрутов магазинов и сетевой аналитики с использованием двух LLM-моделей (Qwen, Llama).

**Длительность**: 4-8 недель (ориентировочно)
**Размер команды**: 3 разработчика + 1 TL/PM
**Методология**: Agile Lite (Kanban, без ежедневных статус-встреч)
**Статус**: Production-Ready

---

## Цели проекта

### Неделя 1-3: MVP (Оптимизация маршрутов) ✅
- [x] Интегрированы 2 LLM-модели (Qwen, Llama)
- [x] Оптимизация маршрутов работает
- [x] Панель управления (MVP) готова
- [x] Команда понимает технический стек
- [x] Тестовое покрытие > 60%

### Неделя 4-6: Production-Ready ✅
- [x] Fallback-механизм (Qwen → Llama → Greedy)
- [x] Docker конфигурация готова
- [x] CI/CD настроен
- [x] Документация обновлена

---

## Архитектура

### Технологический стек

**Backend**:
- Python 3.11+
- FastAPI (REST API)
- SQLAlchemy (ORM)
- Qwen, Llama (LLM-модели, GGUF через llama-cpp-python)
- Pydantic (валидация)

**Frontend**:
- Vue 3 + Vite
- TypeScript
- TailwindCSS
- Axios (HTTP-клиент)

**ML/Analytics**:
- llama-cpp-python
- NumPy
- Бенчмарк моделей

**DevOps**:
- Docker + Docker Compose
- GitHub Actions (CI/CD)
- PostgreSQL
- Redis (кэш)

---

## Структура репозитория

```
T2_project/
├── README.md (этот файл)
├── .gitignore
├── LICENSE
├── .env.example
│
├── docs/
│   ├── AGILE_LITE_QUICKSTART.md
│   ├── EXECUTIVE_SUMMARY.md
│   ├── TEAM_PLAYBOOK.md
│   ├── WEEK_1_PLAN.md
│   ├── WEEK_2_PLAN.md
│   ├── WEEK_3_PLAN.md
│   ├── API_CONTRACT.md
│   ├── ARCHITECTURE.md
│   ├── TEST_PLAN_WEEK1.md
│   ├── TEST_PLAN_WEEK2.md
│   └── TEST_PLAN_WEEK3.md
│
├── backend/
│   ├── src/
│   │   ├── config.py
│   │   ├── models/
│   │   │   ├── llm_client.py (базовый класс)
│   │   │   ├── qwen_client.py (основная модель)
│   │   │   ├── llama_client.py (fallback модель)
│   │   │   ├── schemas.py
│   │   │   └── exceptions.py
│   │   └── routes/
│   │       ├── qwen.py
│   │       └── llama.py
│   ├── tests/
│   │   ├── test_llm_client.py
│   │   ├── test_qwen_client.py
│   │   ├── test_llama_client.py
│   │   ├── test_routes.py
│   │   ├── test_integration.py
│   │   ├── test_optimization_comparison.py
│   │   └── test_quality_evaluator.py
│   ├── main.py
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements/
│       ├── prod/
│       │   └── requirements.txt
│       └── dev/
│           └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── components/
│   │   ├── views/
│   │   ├── services/
│   │   └── tests/
│   ├── public/
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
│
├── ml/
│   ├── benchmarks/
│   │   ├── llm_benchmark.py
│   │   ├── optimization_comparison.py
│   │   └── results.json
│   ├── tests/
│   │   ├── test_ml_ci.py
│   │   └── test_extended_scenarios.py
│   ├── test_models.py
│   └── requirements.txt
│
└── .github/
    └── workflows/
        └── ci.yml
```

---

## Быстрый старт

### Требования
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

### Настройка Backend

```bash
# Клонируем репозиторий
git clone https://github.com/JellyfishKa/T2_project.git
cd T2_project

# Создаем виртуальное окружение
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Устанавливаем зависимости
pip install -r backend/requirements/prod/requirements.txt

# Копируем конфиг
cp .env.example .env
# Отредактируй .env с твоими настройками

# Запускаем backend
cd backend
python -m uvicorn main:app --reload
```

Backend работает на: `http://localhost:8000`

### Настройка Frontend

```bash
# В корне проекта
cd frontend

# Устанавливаем зависимости
npm install

# Запускаем dev-сервер
npm run dev
```

Frontend работает на: `http://localhost:5173`

### Настройка с Docker

```bash
# Копируем конфиг
cp .env.example .env

# Собираем и запускаем все сервисы
docker-compose -f backend/docker-compose.yml up -d

# Просмотр логов
docker-compose -f backend/docker-compose.yml logs -f

# Остановка сервисов
docker-compose -f backend/docker-compose.yml down
```

---

## Ключевые функции

### 1. Поддержка двух LLM-моделей
- **Qwen** (основная модель, лучшее качество оптимизации)
- **Llama** (fallback модель, open-source, максимальная надежность)

Обе модели загружаются в формате GGUF через llama-cpp-python. Автоматический fallback при недоступности основной модели.

### 2. Оптимизация маршрутов
- Вход: Местоположения магазинов, временные окна, ограничения
- Выход: Оптимизированные маршруты с последовательностью и сроками
- LLM-рассуждение + алгоритмическая оптимизация

### 3. Панель аналитики
- Визуализация маршрутов на карте
- Метрики производительности (расстояние, время, стоимость)
- Сравнение результатов нескольких моделей
- Мониторинг производительности в реальном времени

### 4. Стратегия fallback
```
Запрос на оптимизацию маршрута
    |
TRY: Qwen (Primary — лучшее качество)
  |-- Успех -> Возвращаем результат (model_used="Qwen")
  |-- Ошибка -> Следующая модель
    |
TRY: Llama (Fallback — максимальная надежность)
  |-- Успех -> Возвращаем результат (model_used="Llama")
  |-- Ошибка -> Последний резерв
    |
Greedy Algorithm (всегда работает)
  |-- Возвращаем результат (model_used="Greedy")
```

---

## API Endpoints

| Метод | Endpoint | Модель | Назначение |
|-------|----------|--------|------------|
| POST | /api/v1/qwen/optimize | Qwen | Оптимизация маршрута (основная) |
| POST | /api/v1/llama/optimize | Llama | Оптимизация маршрута (надежная) |
| GET | /health | — | Проверка состояния системы |

---

## Тестирование

### Запуск тестов

```bash
# Тесты backend
cd backend
pytest tests/ -v

# Тесты frontend
cd frontend
npm run test

# ML бенчмарки
python ml/benchmarks/llm_benchmark.py --mock
```

### Покрытие тестами

- Backend: 64% покрытия
- Frontend: 70%+ покрытия
- LLM-клиенты: 82%+ покрытия (критический путь)

---

## Статус проекта

| Фаза | Целевое | Статус | Уверенность |
|------|---------|--------|-------------|
| MVP (Оптим. маршрутов) | День 14 | ✅ Завершено | Высокая |
| Production | День 28 | ✅ Готово | Высокая |
| Тестовое покрытие | 60%+ | ✅ 64% | Высокая |
| Docker deployment | День 28 | ✅ Готово | Высокая |

---

## Переменные окружения

Создай файл `.env`:

```env
# LLM Models
QWEN_API_ENDPOINT=local
QWEN_MODEL_ID=qwen2-0_5b-instruct-q4_k_m.gguf

LLAMA_API_ENDPOINT=local
LLAMA_MODEL_ID=Llama-3.2-1B-Instruct-Q4_K_M.gguf

# Database
DATABASE_USER=postgres
DATABASE_PASSWORD=your_secure_password
DATABASE_HOST=localhost
DATABASE_NAME=t2
DATABASE_PORT=5432

# Debug
DEBUG=false
```

---

## Ресурсы моделей

| Модель | GGUF файл | RAM | Диск |
|--------|-----------|-----|------|
| Qwen2-0.5B-Instruct | qwen2-0_5b-instruct-q4_k_m.gguf | ~0.6 GB | ~400 MB |
| Llama-3.2-1B-Instruct | Llama-3.2-1B-Instruct-Q4_K_M.gguf | ~1.2 GB | ~808 MB |
| **Итого** | | **~1.8 GB** | **~1.2 GB** |

Ссылки: [Qwen2-0.5B-Instruct](https://huggingface.co/Qwen/Qwen2-0.5B-Instruct), [Llama-3.2-1B-Instruct](https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct).

---

## Документация

### Для разработчиков

- **[AGILE_LITE_QUICKSTART.md](docs/AGILE_LITE_QUICKSTART.md)** — Как мы работаем (процесс)
- **[TEAM_PLAYBOOK.md](docs/TEAM_PLAYBOOK.md)** — Ответственность ролей
- **[API_CONTRACT.md](docs/API_CONTRACT.md)** — Спецификация API
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** — Дизайн системы
- **[TEST_PLAN_WEEK1.md](docs/TEST_PLAN_WEEK1.md)** — Тест-план LLM клиентов
- **[MODEL_SETUP_GUIDE.md](docs/MODEL_SETUP_GUIDE.md)** — Руководство по установке моделей

### Для планирования

- **[EXECUTIVE_SUMMARY.md](docs/EXECUTIVE_SUMMARY.md)** — Обзор проекта
- **[WEEK_1_PLAN.md](docs/WEEK_1_PLAN.md)** — Детали первой недели
- **[WEEK_2_PLAN.md](docs/WEEK_2_PLAN.md)** — Планирование MVP
- **[WEEK_3_PLAN.md](docs/WEEK_3_PLAN.md)** — Production-Ready

---

## Поддержка

**Вопросы по проекту**: Обратись к [@maklakov_tkdrm] в TG
**Технические проблемы**: Напиши в #blockers
**Проверка кода**: Отметь рецензента в #code-review
**Ошибки**: Создай GitHub issue

---

## Лицензия

Этот проект является собственностью. См. файл LICENSE.

---

## Команда

- **Backend**: [Роман Кижаев]
- **Frontend**: [Владислав Наумкин]
- **ML/Analytics**: [Дмитрий Мукасеев]
- **TL/PM**: [Сергей Маклаков]

---

*Последнее обновление: 16 февраля 2026 года*