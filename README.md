# T2 Розничная сеть

**AI-powered оптимизация маршрутов и сетевая аналитика для розничной торговли**

## Описание проекта

T2 Розничная сеть — это комплексная платформа на основе искусственного интеллекта для оптимизации маршрутов магазинов и сетевой аналитики с использованием двух LLM-моделей (Qwen, Llama).

**Длительность**: 4-8 недель (ориентировочно)
**Размер команды**: 3 разработчика + 1 TL/PM
**Методология**: Agile Lite (Kanban, без ежедневных статус-встреч)
**Статус**: Активная разработка

---

## Цели проекта

### Неделя 1-3: MVP (Оптимизация маршрутов)
- [x] Интегрированы 2 LLM-модели (Qwen, Llama)
- [ ] Оптимизация маршрутов работает
- [ ] Панель управления (MVP) готова
- [x] Команда понимает технический стек

### Неделя 4-6: Production-Ready
- [ ] Оптимизация маршрутов оптимизирована (производительность)
- [ ] Полный функционал панели управления
- [ ] Производительность протестирована
- [ ] Готово к продакшену

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
- PyTorch, Transformers, Accelerate
- NumPy, Pandas, scikit-learn
- Hugging Face Hub
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
│   └── TEST_PLAN_WEEK1.md
│
├── backend/
│   ├── src/
│   │   ├── main.py
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
│   │   ├── test_integration.py
│   │   ├── test_optimization_comparison.py
│   │   └── test_quality_evaluator.py
│   ├── main.py
│   └── requirements/
│       └── prod/
│           └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── components/
│   │   ├── views/
│   │   │   └── OptimizeView.vue
│   │   ├── services/
│   │   ├── styles/
│   │   └── tests/
│   │       └── integration/
│   │           └── frontend-backend.spec.ts
│   ├── public/
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── ml/
│   ├── benchmarks/
│   │   ├── llm_benchmark.py
│   │   ├── optimization_comparison.py
│   │   ├── generate_analysis_report.py
│   │   ├── README.md
│   │   └── results.json
│   ├── models/
│   ├── notebooks/
│   ├── tests/
│   ├── test_models.py
│   ├── requirements.txt
│   └── README.md
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
# Отредактируй .env с твоими API токенами и путями к моделям

# Запускаем backend
cd backend
python -m uvicorn src.main:app --reload
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

### Настройка ML окружения

```bash
# Создаем отдельное виртуальное окружение для ML
python -m venv ml_env
source ml_env/bin/activate  # Windows: ml_env\Scripts\activate

# Устанавливаем зависимости
pip install -r ml/requirements.txt

# Проверяем доступность моделей
python ml/test_models.py

# Запускаем бенчмарк
python ml/benchmarks/llm_benchmark.py
```

### Настройка с Docker

```bash
# Собираем и запускаем все сервисы
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка сервисов
docker-compose down
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

Все endpoints возвращают поля `model_used` и `fallback_reason` в ответах.

---

## API Endpoints

| Метод | Endpoint | Модель | Назначение |
|-------|----------|--------|------------|
| POST | /qwen/optimize | Qwen | Оптимизация маршрута (основная) |
| POST | /llama/optimize | Llama | Оптимизация маршрута (надежная) |
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
python ml/benchmarks/llm_benchmark.py

# Бенчмарк с mock данными
python ml/benchmarks/llm_benchmark.py --mock

# Бенчмарк клиентов backend
python ml/benchmarks/llm_benchmark.py --backend --iterations 2
```

### Покрытие тестами

- Backend: 80%+ покрытия
- Frontend: 70%+ покрытия
- LLM-клиенты: 100% покрытия (критический путь)

---

## Процесс разработки

### Agile Lite процесс

**Понедельник 10:00 — Планирование** (30 мин)
- Обзор бэклога
- Команда выбирает задачи на неделю
- Переместить в колонку TO DO в Jira

**Ежедневно** (асинхронно):
- Проверить Jira доску за своими задачами
- Переместить задачи через: TO DO -> IN PROGRESS -> REVIEW -> DONE
- Прокомментировать блокеры в #blockers Telegram

**Пятница 16:00 — Демо + Ретроспектива** (1 час)
- Демонстрация завершенных функций
- Обратная связь ретроспективы
- План улучшений

### Каналы коммуникации

- **#blockers**: Только чрезвычайные ситуации
- **#code-review**: Проверка PR
- **#general**: Объявления
- **#t2-backend**: Обсуждение backend
- **#t2-frontend**: Обсуждение frontend
- **#t2-ml**: Обсуждение ML

---

## Текущие вехи

### Неделя 1-2
- [x] Настройка инфраструктуры
- [x] Получение доступа к LLM (Qwen, Llama)
- [x] Структура backend проекта
- [x] Базовый макет frontend
- [x] Внедрение Agile Lite

### Неделя 3 — MVP
- [ ] Оптимизация маршрутов работает
- [ ] Панель управления 80% готова
- [x] Все 2 LLM-модели интегрированы
- [ ] MVP готов к демо

### Неделя 4-6
- [ ] Улучшение производительности
- [ ] Финализация панели управления
- [ ] Тестирование производительности
- [ ] Настройка деплоя

---

## Документация

### Для разработчиков

- **[AGILE_LITE_QUICKSTART.md](docs/AGILE_LITE_QUICKSTART.md)** — Как мы работаем (процесс)
- **[TEAM_PLAYBOOK.md](docs/TEAM_PLAYBOOK.md)** — Ответственность ролей
- **[API_CONTRACT.md](docs/API_CONTRACT.md)** — Спецификация API
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** — Дизайн системы
- **[TEST_PLAN_WEEK1.md](docs/TEST_PLAN_WEEK1.md)** — Тест-план LLM клиентов
- **[MODEL_SETUP_GUIDE.md](docs/MODEL_SETUP_GUIDE.md)** — Руководство по установке моделей
- **[server-guide.md](docs/server-guide.md)** — Руководство по серверу

### Для планирования

- **[EXECUTIVE_SUMMARY.md](docs/EXECUTIVE_SUMMARY.md)** — Обзор проекта
- **[WEEK_1_PLAN.md](docs/WEEK_1_PLAN.md)** — Детали первой недели
- **[WEEK_2_PLAN.md](docs/WEEK_2_PLAN.md)** — Планирование MVP
- **[WEEK_3_PLAN.md](docs/WEEK_3_PLAN.md)** — Фаза полировки

### ML документация

- **[ml/README.md](ml/README.md)** — ML окружение и модели
- **[ml/benchmarks/README.md](ml/benchmarks/README.md)** — Бенчмарк LLM

---

## Переменные окружения

Создай файл `.env`:

```env
# Backend
DATABASE_URL=postgresql://user:password@localhost/t2_db
BACKEND_PORT=8000

# LLM Модели (Qwen)
QWEN_API_ENDPOINT=local
QWEN_MODEL_ID=qwen2-0_5b-instruct-q4_k_m.gguf

# LLM Модели (Llama)
LLAMA_API_ENDPOINT=local
LLAMA_MODEL_ID=Llama-3.2-1B-Instruct-Q4_K_M.gguf

# Hugging Face
HF_TOKEN=your_hf_token

# Frontend
FRONTEND_PORT=5173
VITE_API_URL=http://localhost:8000

# Деплой
ENVIRONMENT=development  # или production
DEBUG=true
```

---

## Ресурсы моделей

| Модель | VRAM (ориентир) | RAM (загрузка) | GGUF файл | Примечание |
|--------|-----------------|----------------|-----------|------------|
| Qwen2-0.5B-Instruct | ~2 GB | ~4 GB | ~400 MB | Удобна для локального инференса |
| Llama-3.2-1B-Instruct | ~4 GB | ~6 GB | ~808 MB | Community GGUF, скачивается без логина |

Ссылки: [Qwen2-0.5B-Instruct](https://huggingface.co/Qwen/Qwen2-0.5B-Instruct), [Llama-3.2-1B-Instruct](https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct).

---

## Статус проекта

| Фаза | Целевое | Статус | Уверенность |
|------|---------|--------|-------------|
| MVP (Оптим. маршрутов) | День 14 | В работе | Средняя |
| Production | День 28 | В работе | Средняя |
| Скорость команды | 12+ задач/неделя | В работе | Высокая |
| Моральный дух | 8/10 | В работе | Высокая |

---

## Внесение вклада

### Перед началом

1. Прочитай [TEAM_PLAYBOOK.md](docs/TEAM_PLAYBOOK.md)
2. Проверь Jira доску для назначенных задач
3. Создай ветку функции: `git checkout -b feature/task-name`

### Процесс проверки кода

1. Залей на GitHub
2. Создай PR с описанием
3. Отметь рецензента в #code-review Telegram
4. Цель: проверка кода в течение 4 часов
5. Слияние после одобрения

### Соглашение о коммитах

```
[TICKET]: Краткое описание

Более подробное описание изменений.
Исправления #TICKET если применимо.
```

Пример:
```
BE-4: Реализация QwenClient

- Реализовать класс QwenClient (PRIMARY модель)
- Добавить обработку ошибок и retry логику
- Добавить unit тесты
```

---

## Поддержка

**Вопросы по проекту**: Обратись к [@maklakov_tkdrm] в TG
**Технические проблемы**: Напиши в #blockers
**Проверка кода**: Отметь рецензента в #code-review
**Ошибки**: Создай GitHub issue

---

## Ресурсы

- [Документация FastAPI](https://fastapi.tiangolo.com/)
- [Руководство Vue 3](https://vuejs.org/guide/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [Hugging Face Hub](https://huggingface.co/docs)
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python)

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

**Вопросы?** Сначала посмотри документы, потом напиши в Telegram!

**Давайте отправим!**

---

*Последнее обновление: 16 февраля 2026 года*
