# 📋 НЕДЕЛЯ 1: ДЕТАЛЬНЫЙ ПЛАН ТАСК

## 📊 ОБЗОР НЕДЕЛИ 1

**Цель**: Рабочее dev окружение + все 3 НОВЫХ LLM модели доступны

**Velocity**: 12-15 задач на неделю (в неделе 5 дней)

**Распределение**:
- Backend: 6 задач (UPDATED для новых моделей)
- Frontend: 5 задач (same)
- ML: 3 задачи (UPDATED для новых моделей)
- QA/PM: 1 задача (UPDATED для новых моделей)

---

## ✅ BACKEND ТАСКИ (6 задач)

### BE-1: Создание GitHub репозитория и инициализация проекта

**Приоритет**: 🔴 HIGH

**Оценка**: 2 часа

**Assignee**: Backend разработчик

**Описание**:
Создать GitHub репозиторий для проекта T2 Розничная сеть с правильной структурой папок, инициализировать Python проект и настроить базовые конфиги. Это основание для всех остальных backend задач.

**Acceptance Criteria**:
- ✅ GitHub репозиторий создан (название: t2-retail-network)
- ✅ Структура папок создана: backend/, frontend/, ml/, docs/, .github/workflows/
- ✅ Python виртуальное окружение создано (venv)
- ✅ requirements.txt создан с базовыми зависимостями (FastAPI, SQLAlchemy, Pydantic, uvicorn)
- ✅ .gitignore файл добавлен (с __pycache__, venv, .env, и т.д)
- ✅ README.md скопирован из документации в репо
- ✅ Репо готов к использованию (все файлы закоммичены и запушены)

**Ссылки на документацию**:
- README.md (структура репо): https://github.com/[username]/t2-retail-network

**Примечания**:
- Git commits должны быть на русском (пример: "init: Инициализация проекта T2")
- Не забудь про .env.example файл (без реальных токенов!)

---

### BE-2: Получение доступа к LLM сервисам и настройка токенов

**Приоритет**: 🔴 HIGH

**Оценка**: 4 часа

**Assignee**: Backend разработчик

**Описание**:
Получить доступ к трём НОВЫМ LLM сервисам **(Qwen, T-Pro, Llama)** и настроить токены/ключи. Это критично для всех последующих интеграций LLM. Может потребоваться работа с системными администраторами или регистрация на внешних сервисах.

**Acceptance Criteria**:
- ✅ **Qwen** токен/доступ получен и проверен (успешный тестовый запрос к API)
- ✅ **T-Pro** токен/доступ получен и проверен
- ✅ **Llama** модель доступна локально (или доступ к облачному Llama)
- ✅ .env.example обновлён со всеми необходимыми переменными
  - QWEN_API_KEY или QWEN_TOKEN
  - TPRO_API_KEY или TPRO_TOKEN
  - LLAMA_MODEL_PATH или LLAMA_API_URL
- ✅ config.py создан в backend/src/ с загрузкой токенов из .env
- ✅ Каждый токен задокументирован с инструкциями по обновлению

**Ссылки на документацию**:
- ARCHITECTURE.md (раздел "LLM Client Interface"): docs/ARCHITECTURE.md
- API_CONTRACT.md: docs/API_CONTRACT.md

**Примечания**:
- Токены НЕ должны быть в GitHub (только в .env.example как примеры)
- Документируй ссылки на документацию каждого сервиса для будущих разработчиков
- Если какой-то токен недоступен в Day 1 — используй mock для тестирования

**Model Access Instructions**:
```
Qwen: https://dashscope.console.aliyun.com (requires API key)
T-Pro: https://console.anthropic.com or similar
Llama: Local installation (llama-cpp-python) or API endpoint
```

**Blockers & Risks**:
- ⚠️ Qwen может потребовать много времени на утверждение
- ⚠️ Mitigation: подготовь T-Pro как fallback

---

### BE-3: Создание базового LLMClient интерфейса (абстрактный класс)

**Приоритет**: 🔴 HIGH

**Оценка**: 3 часа

**Assignee**: Backend разработчик

**Зависит от**: BE-1, BE-2

**Описание**:
Создать абстрактный базовый класс LLMClient в backend/src/models/llm_client.py. Это интерфейс, который будут реализовывать все конкретные LLM клиенты **(Qwen, T-Pro, Llama)**. Правильная архитектура здесь это фундамент для fallback механизма.

**Acceptance Criteria**:
- ✅ Файл backend/src/models/llm_client.py создан
- ✅ Класс LLMClient с @abstractmethod создан в Python
- ✅ Минимум 3 абстрактных метода определены:
  - `async def generate_route(locations: List[Location]) -> str`
  - `async def analyze_metrics(data: Dict) -> str`
  - `async def health_check() -> bool`
- ✅ Каждый метод имеет docstring с объяснением
- ✅ Enum для статусов (SUCCESS, FAILURE, TIMEOUT) создан
- ✅ Unit тесты написаны (test_llm_clients.py)

**Ссылки на документацию**:
- ARCHITECTURE.md (раздел "LLM Client Interface"): docs/ARCHITECTURE.md

**Примечания**:
- Используй Python ABC (Abstract Base Classes) для правильной реализации
- Docstring должен быть на русском и английском
- Не добавляй реальную логику LLM вызовов — только интерфейс

**Code Style**:
- Следуй PEP 8
- Type hints обязательны
- Комментарии на русском где нужна уточнение

---

### BE-4: Реализация QwenClient (PRIMARY MODEL)

**Приоритет**: 🔴 HIGH

**Оценка**: 6 часов

**Assignee**: Backend разработчик

**Зависит от**: BE-2, BE-3

**Описание**:
Реализовать конкретный класс **QwenClient** который наследуется от LLMClient и работает с **Qwen API** (Alibaba). Это НОВАЯ основная LLM модель для проекта (заменяет GigaChat).

**Acceptance Criteria**:
- ✅ Файл backend/src/models/qwen_client.py создан
- ✅ Класс QwenClient наследуется от LLMClient
- ✅ Токен загружается из config (не hardcoded)
  - QWEN_API_KEY из .env
- ✅ Метод generate_route() реализован с реальным API вызовом к Qwen
- ✅ Обработка ошибок добавлена (timeout, auth error, rate limit, API errors)
- ✅ Логирование добавлено (логируются все вызовы и результаты)
- ✅ Unit тесты написаны (test_qwen_client.py)
  - Успешный API запрос
  - Обработка ошибок (400, 401, 429, 500)
  - Timeout обработка
- ✅ Успешный тестовый запрос документирован

**Ссылки на документацию**:
- Qwen API docs: https://dashscope.console.aliyun.com
- ARCHITECTURE.md: docs/ARCHITECTURE.md
- API_CONTRACT.md: docs/API_CONTRACT.md

**Примечания**:
- Используй асинхронные вызовы (async/await)
- Логирование должно быть достаточным для отладки
- Mock ответы для тестирования (если реальное API недоступно)
- Qwen это PRIMARY модель, поэтому должна быть надежной

**Code Example**:
```python
class QwenClient(LLMClient):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/"
    
    async def generate_route(self, locations: List[Location]) -> str:
        # Call Qwen API and return optimized route
        pass
```

---

### BE-4.5: Реализация T-ProClient (SECONDARY MODEL)

**Приоритет**: 🔴 HIGH

**Оценка**: 5 часов

**Assignee**: Backend разработчик

**Зависит от**: BE-2, BE-3

**Описание**:
Реализовать конкретный класс **T-ProClient** который наследуется от LLMClient и работает с T-Pro API. Это НОВАЯ вторичная модель для проекта (заменяет Cotype как secondary fallback).

**Acceptance Criteria**:
- ✅ Файл backend/src/models/tpro_client.py создан
- ✅ Класс T-ProClient наследуется от LLMClient
- ✅ Токен загружается из config (не hardcoded)
  - TPRO_API_KEY или аналог из .env
- ✅ Метод generate_route() реализован с реальным API вызовом к T-Pro
- ✅ Обработка ошибок добавлена (timeout, auth error, rate limit)
- ✅ Логирование добавлено
- ✅ Unit тесты написаны (test_tpro_client.py)
- ✅ Успешный тестовый запрос документирован
- ✅ Response time документирован (goal: < 2 sec)

**Ссылки на документацию**:
- T-Pro API docs: [link to documentation]
- ARCHITECTURE.md: docs/ARCHITECTURE.md

**Примечания**:
- T-Pro используется как fallback от Qwen, поэтому должна быть быстрой
- Используй асинхронные вызовы
- Документируй особенности T-Pro API

---

### BE-5: Реализация LlamaClient (FALLBACK MODEL)

**Приоритет**: 🔴 HIGH

**Оценка**: 6 часов

**Assignee**: Backend разработчик

**Зависит от**: BE-2, BE-3

**Описание**:
Реализовать конкретный класс **LlamaClient** который наследуется от LLMClient и работает с Llama моделью (open-source). Это НОВАЯ резервная модель для проекта (заменяет Cotype как fallback для максимальной надежности).

**Acceptance Criteria**:
- ✅ Файл backend/src/models/llama_client.py создан
- ✅ Класс LlamaClient наследуется от LLMClient
- ✅ Модель/доступ загружается из config
  - LLAMA_MODEL_PATH (локально) или LLAMA_API_URL (облачно)
- ✅ Метод generate_route() реализован
- ✅ Обработка ошибок добавлена
- ✅ Логирование добавлено
- ✅ Unit тесты написаны (test_llama_client.py)
- ✅ Быстрый response time документирован (goal: < 5 sec)
- ✅ Надежность документирована (99%+ uptime для локальной модели)

**Ссылки на документацию**:
- Llama docs: https://github.com/ggerganov/llama.cpp
- ARCHITECTURE.md: docs/ARCHITECTURE.md

**Примечания**:
- Llama это финальный fallback
- Может быть локальная модель (llama-cpp-python) для максимальной надежности
- Или облачный endpoint, но ОЧЕНЬ надежный
- Надежность > производительность
- Документируй требования к памяти/ресурсам

**Why Llama as Fallback**:
- Open-source (нет dependency на external service)
- Может работать локально (100% control)
- Если что-то сломалось с Qwen/T-Pro → Llama спасет

---

### BE-6: Настройка Docker и Docker Compose для dev окружения

**Приоритет**: 🟡 MEDIUM

**Оценка**: 4 часа

**Assignee**: Backend разработчик

**Зависит от**: BE-1

**Описание**:
Создать Dockerfile для backend и docker-compose.yml для локального развертывания. Это упростит setup для остальной команды и обеспечит консистентность dev окружения.

**Acceptance Criteria**:
- ✅ Dockerfile создан (backend/Dockerfile)
- ✅ docker-compose.yml создан в корне проекта
- ✅ Сервисы в Docker Compose:
  - backend (FastAPI, порт 8000)
  - frontend (Vue, порт 5173)
  - postgres (database, порт 5432)
- ✅ All services успешно запускаются: `docker compose up`
- ✅ Backend API доступен на localhost:8000
- ✅ Health check endpoint работает: GET /health
- ✅ .env.example обновлён с DATABASE_URL

**Ссылки на документацию**:
- ARCHITECTURE.md (раздел "Docker Setup"): docs/ARCHITECTURE.md

**Примечания**:
- Используй multi-stage builds для optimization
- Environment variables должны передаваться через Docker Compose
- Volume маппинг для development (code changes без rebuild)
- Поддержка всех 3 новых LLM моделей (Qwen, T-Pro, Llama)

**Testing Checklist**:
- ✅ Docker images собираются без ошибок
- ✅ Services стартуют успешно
- ✅ Можешь подключиться к каждому сервису

---

## 🎨 FRONTEND ТАСКИ (5 задач)

### FE-1: Инициализация Vue 3 проекта с Vite

**Приоритет**: 🔴 HIGH

**Оценка**: 2 часа

**Assignee**: Frontend разработчик

**Зависит от**: BE-1

**Описание**:
Создать новый Vue 3 проект с Vite в папке frontend/. Настроить TypeScript, TailwindCSS и базовую структуру компонентов. Это основание для всех frontend задач.

**Acceptance Criteria**:
- ✅ Vue 3 + Vite проект создан в папке frontend/
- ✅ TypeScript configured (tsconfig.json)
- ✅ TailwindCSS установлен и настроен
- ✅ Папки структура создана: src/components/, src/views/, src/services/, src/styles/
- ✅ Базовый App.vue создан с routing
- ✅ package.json содержит все необходимые dependencies
- ✅ npm run dev работает без ошибок
- ✅ Vue DevTools интеграция настроена

**Ссылки на документацию**:
- ARCHITECTURE.md (раздел "Frontend Architecture"): docs/ARCHITECTURE.md

**Примечания**:
- .gitignore должен исключать node_modules, dist/, и т.д
- Убедись что TypeScript strict mode включен

---

### FE-2: Создание базового layout и навигации

**Приоритет**: 🟡 MEDIUM

**Оценка**: 4 часа

**Assignee**: Frontend разработчик

**Зависит от**: FE-1

**Описание**:
Создать основной Layout компонент с Header, Sidebar (опционально) и main content area. Добавить базовую навигацию между страницами (Home, Dashboard, Optimize, Analytics).

**Acceptance Criteria**:
- ✅ Компонент Layout.vue создан в src/components/
- ✅ Header компонент создан с логотипом и навигацией
- ✅ Vue Router настроен (src/router/index.ts)
- ✅ Минимум 3 view страницы созданы:
  - Home.vue (landing page)
  - Dashboard.vue (placeholder)
  - OptimizeView.vue (placeholder)
- ✅ Навигация работает (клик по ссылке меняет страницу)
- ✅ Responsive дизайн (работает на мобильных)
- ✅ TailwindCSS используется для стилей

**Ссылки на документацию**:
- ARCHITECTURE.md (раздел "Frontend Architecture"): docs/ARCHITECTURE.md

**Примечания**:
- Не нужна функциональность, только UI structure
- Используй Tailwind utility classes
- Mobile-first подход

---

### FE-3: Создание API сервиса с mock данными

**Приоритет**: 🟡 MEDIUM

**Оценка**: 5 часов

**Assignee**: Frontend разработчик

**Зависит от**: FE-1

**Описание**:
Создать src/services/api.ts файл с axios клиентом и mock interceptor. В Неделе 1 используем mock данные, в Неделе 2 заменим на реальный backend.

**Acceptance Criteria**:
- ✅ src/services/api.ts создан с axios инстансом
- ✅ Base URL настроен (VITE_API_URL из .env)
- ✅ Mock interceptor добавлен для development
- ✅ Типы данных (interfaces) созданы:
  - Location, Route, Metric, BenchmarkResult (из API_CONTRACT)
- ✅ Mock данные созданы в src/services/mockData.ts
- ✅ Функции-обёртки для API вызовов:
  - `fetchRoutes()`, `optimizeRoute()`, `fetchMetrics()`, `runBenchmark()`
- ✅ Error handling реализирован
- ✅ Mock данные возвращают реалистичные значения

**Ссылки на документацию**:
- API_CONTRACT.md: docs/API_CONTRACT.md
- ARCHITECTURE.md: docs/ARCHITECTURE.md

**Примечания**:
- Mock должен работать как реальный API (async, с задержкой)
- В Неделе 2 просто удалим mock interceptor и используем реальный backend

**Mock Data Checklist**:
- ✅ 5+ магазинов с координатами
- ✅ 2-3 оптимизированных маршрутов
- ✅ Метрики для каждого маршрута
- ✅ Результаты бенчмарков для 3 моделей (Qwen, T-Pro, Llama)

---

### FE-4: Создание страницы Dashboard с компонентами

**Приоритет**: 🟡 MEDIUM

**Оценка**: 6 часов

**Assignee**: Frontend разработчик

**Зависит от**: FE-2, FE-3

**Описание**:
Создать Dashboard страницу с компонентами для отображения маршрутов, метрик и результатов. Пока использует mock данные.

**Acceptance Criteria**:
- ✅ Страница src/views/Dashboard.vue создана
- ✅ Компоненты созданы:
  - RouteList.vue (список маршрутов)
  - RouteMetrics.vue (метрики: расстояние, время, стоимость)
  - ModelComparison.vue (сравнение моделей)
- ✅ Dashboard загружает mock данные через API сервис
- ✅ Данные отображаются в таблицах или карточках
- ✅ Responsive дизайн (работает на мобильных и десктопах)
- ✅ Нет ошибок в консоли

**Ссылки на документацию**:
- API_CONTRACT.md (data models): docs/API_CONTRACT.md
- ARCHITECTURE.md: docs/ARCHITECTURE.md

**Примечания**:
- Пока это просто отображение данных
- В Неделе 2 добавим интерактивность и сохранение состояния

---

### FE-5: Создание формы для оптимизации маршрутов (UI без логики)

**Приоритет**: 🟡 MEDIUM

**Оценка**: 5 часов

**Assignee**: Frontend разработчик

**Зависит от**: FE-2, FE-3

**Описание**:
Создать страницу OptimizeView.vue с формой для ввода магазинов и ограничений. Пока без логики отправки на backend.

**Acceptance Criteria**:
- ✅ Страница src/views/OptimizeView.vue создана
- ✅ Компоненты созданы:
  - OptimizationForm.vue (основная форма с полями)
  - LocationInput.vue (для добавления магазинов)
  - ConstraintsPanel.vue (для установки ограничений)
- ✅ Поля формы:
  - Название маршрута
  - Список магазинов (с возможностью добавления/удаления)
  - Временные окна
  - Вместимость машины
  - Max расстояние
- ✅ Валидация формы (простая, на frontend)
- ✅ Кнопка "Оптимизировать" (пока без функции, просто UI)
- ✅ Responsive дизайн
- ✅ Нет ошибок в консоли

**Ссылки на документацию**:
- API_CONTRACT.md (Location, constraints models): docs/API_CONTRACT.md

**Примечания**:
- В Неделе 2 добавим функцию отправки на backend
- Валидация пока простая (не пусто, корректные числа)
- Mock submit обработка (console.log)

---

## 🤖 ML ТАСКИ (3 задачи) -

### ML-1: Подготовка окружения и загрузка моделей

**Приоритет**: 🔴 HIGH

**Оценка**: 3 часа

**Assignee**: ML разработчик

**Зависит от**: BE-1, BE-2

**Описание**:
Настроить Python окружение для ML работы, загрузить и протестировать все 3 НОВЫХ LLM модели **(Qwen, T-Pro, Llama)** локально. Убедиться что все модели доступны и работают.

**Acceptance Criteria**:
- ✅ ml/ папка структура создана: benchmarks/, models/, notebooks/
- ✅ ml/requirements.txt создан с зависимостями (scikit-learn, numpy, pandas, etc)
- ✅ Python виртуальное окружение создано для ML проекта
- ✅ Все 3 НОВЫХ модели успешно загружены и доступны:
  - **Qwen** (через API, токен работает)
  - **T-Pro** (через API или локально)
  - **Llama** (локально через llama-cpp-python или облачный endpoint)
- ✅ Простой test script создан (ml/test_models.py) который проверяет доступность каждой модели
- ✅ Логирование добавлено (какая модель загружена, статус, response time)
- ✅ Test script успешно запускается и выводит статус каждой модели

**Ссылки на документацию**:
- ARCHITECTURE.md (раздел "LLM Models"): docs/ARCHITECTURE.md

**Примечания**:
- Убедись что модели загружаются без ошибок
- Документируй требования к памяти/ресурсам для каждой модели
- Если модель долго загружается — кэшируй её локально
- Test script должен выводить информацию о каждой модели:
  ```
  Qwen: ✓ Available (API key verified)
  T-Pro: ✓ Available (API key verified)
  Llama: ✓ Available (Loaded from /path/to/model)
  ```

---

### ML-2: Создание benchmark скрипта для трёх НОВЫХ моделей

**Приоритет**: 🟡 MEDIUM

**Оценка**: 6 часов

**Assignee**: ML разработчик

**Зависит от**: ML-1, BE-3

**Описание**:
Создать скрипт ml/benchmarks/llm_benchmark.py который запускает тесты на всех 3 НОВЫХ моделях (Qwen, T-Pro, Llama) и собирает метрики. Метрики: время ответа, качество ответа, стоимость (если есть).

**Acceptance Criteria**:
- ✅ Файл ml/benchmarks/llm_benchmark.py создан
- ✅ Функция run_benchmark() реализована с параметрами:
  - num_iterations (количество тестов на модель)
  - test_data (тестовые данные)
- ✅ Для КАЖДОЙ из 3 НОВЫХ моделей собираются метрики:
  - **Qwen**: response_time_ms, quality_score, success_rate, cost_rub
  - **T-Pro**: response_time_ms, quality_score, success_rate, cost_rub
  - **Llama**: response_time_ms, quality_score, success_rate, cost_rub
- ✅ Плюс baseline для сравнения
- ✅ Результаты сохраняются в ml/benchmarks/results.json
- ✅ Логирование добавлено (прогресс бенчмарка, какая модель сейчас тестируется)
- ✅ Обработка ошибок (если модель недоступна, используй mock)
- ✅ Скрипт успешно запускается: `python ml/benchmarks/llm_benchmark.py`

**Ссылки на документацию**:
- ARCHITECTURE.md: docs/ARCHITECTURE.md

**Примечания**:
- Test data должны быть реалистичными (примеры маршрутов)
- Quality score может быть базирован на длине ответа, наличие ошибок, и т.д
- Бенчмарк может занять 10-30 минут на 5 итераций
- Результаты будут использованы в ML-3 для рекомендаций

**Benchmark Output Example**:
```json
{
  "timestamp": "2026-01-10T15:30:00Z",
  "results": [
    {
      "model": "Qwen",
      "iterations": 5,
      "avg_response_time_ms": 2345,
      "quality_score": 92,
      "success_rate": 100,
      "cost_rub": 45
    },
    {
      "model": "T-Pro",
      "avg_response_time_ms": 1800,
      "quality_score": 88,
      "success_rate": 100,
      "cost_rub": 60
    },
    {
      "model": "Llama",
      "avg_response_time_ms": 4500,
      "quality_score": 85,
      "success_rate": 100,
      "cost_rub": 0
    }
  ]
}
```

---

### ML-3: Анализ результатов бенчмарков и создание отчёта 

**Приоритет**: 🟡 MEDIUM

**Оценка**: 4 часа

**Assignee**: ML разработчик

**Зависит от**: ML-2

**Описание**:
Проанализировать результаты бенчмарков из ml/benchmarks/results.json и создать отчёт с рекомендациями какую модель использовать как primary и когда использовать fallback. **Важно: Рекомендация должна основываться на трёх НОВЫХ моделях (Qwen, T-Pro, Llama).**

**Acceptance Criteria**:
- ✅ Файл ml/benchmarks/analysis_report.md создан
- ✅ Отчёт содержит:
  - Сравнительную таблицу (время, качество, стоимость для **Qwen, T-Pro, Llama**)
  - Графики (если возможно): время ответа, качество score, стоимость
  - Выводы: какая модель лучшая для primary, какие для fallback
  - **Рекомендация по использованию**:
    - Primary: **Qwen** (лучшее качество)
    - Secondary: **T-Pro** (лучшая скорость)
    - Fallback: **Llama** (лучшая надежность)
- ✅ Документированы edge cases (когда модель падает, медленная, и т.д)
- ✅ Рекомендация Primary/Fallback/Tertiary модели указана в отчёте
- ✅ Отчёт на русском языке

**Ссылки на документацию**:
- ARCHITECTURE.md: docs/ARCHITECTURE.md

**Примечания**:
- Графики могут быть ASCII art если нет matplotlib
- Выводы должны быть обоснованы данными
- Рекомендация будет использована в Backend для настройки fallback механизма

**Рекомендованная архитектура**:
```
Request optimizes route
    ↓
TRY: Qwen (best quality) - PRIMARY
  ├─ Works? Return ✓
  └─ Fails → Next

TRY: T-Pro (fast) - SECONDARY
  ├─ Works? Return ✓
  └─ Fails → Next

TRY: Llama (reliable) - FALLBACK
  ├─ Works? Return ✓
  └─ Fails → Return error
```

---

## 📊 QA/PM ТАСКИ (1 задача) - 

### QA-1: Создание Test Plan для LLM клиентов и настройка CI 

**Приоритет**: 🟡 MEDIUM

**Оценка**: 8 часов

**Assignee**: QA/PM

**Зависит от**: BE-1

**Описание**:
Создать test plan для всех 3 НОВЫХ LLM клиентов (Qwen, T-Pro, Llama), настроить pytest, и создать GitHub Actions workflow для автоматического запуска тестов при push. Это обеспечит качество кода с самого начала.

**Acceptance Criteria**:
- ✅ Файл docs/TEST_PLAN_WEEK1.md создан с test cases для всех 3 новых моделей
- ✅ Test cases включают (для КАЖДОЙ модели):
  - Успешный запрос к API (mock если нужно)
  - Обработка ошибок (400, 401, 429, 500)
  - Timeout обработка
  - Invalid input обработка
  - **NEW: Fallback механизм (если Qwen падает → T-Pro, если T-Pro падает → Llama, если Llama падает → ошибка)**
  - **NEW: Model initialization test (все 3 модели инициализируются корректно)**
- ✅ pytest установлен и настроен (pytest.ini создан)
- ✅ Минимум 80% code coverage для LLM клиентов
- ✅ GitHub Actions workflow создан (.github/workflows/ci.yml)
- ✅ Workflow запускает тесты при каждом push
  - **Тесты для Qwen**
  - **Тесты для T-Pro**
  - **Тесты для Llama**
  - **Тесты fallback механизма**
- ✅ Workflow логирует результаты (pass/fail)
- ✅ Pull Request не может быть merged если тесты падают
- ✅ Документация по запуску тестов локально (README)

**Ссылки на документацию**:
- ARCHITECTURE.md (Testing Strategy): docs/ARCHITECTURE.md

**Примечания**:
- Tests должны быть быстрыми (< 30 сек на всех)
- Mock API responses где нужно (чтобы не зависеть от реальных сервисов)
- Coverage отчет должен генерироваться и просматриваться
- **КРИТИЧНО**: Fallback механизм должен быть протестирован
  - Test: Qwen успешен → используется Qwen
  - Test: Qwen fails → T-Pro используется
  - Test: T-Pro fails → Llama используется
  - Test: Все LLM fails → возвращается ошибка

**Testing Checklist**:
- ✅ Локальные тесты запускаются успешно
- ✅ GitHub Actions workflow работает
- ✅ Coverage >= 80%
- ✅ Тесты reproducible (одинаковые результаты при повторном запуске)
- ✅ Fallback тесты проходят

---

## 📋 SUMMARY ТАБЛИЦА 

| ID | Название | Приоритет | Часы | Assignee | Зависит от |
|----|----------|-----------|------|----------|-----------|
| BE-1 | GitHub + проект инициализация | 🔴 HIGH | 2ч | Backend | - |
| BE-2 | **NEW LLM токены (Qwen/T-Pro/Llama)** | 🔴 HIGH | 4ч | Backend | BE-1 |
| BE-3 | LLMClient интерфейс | 🔴 HIGH | 3ч | Backend | BE-1, BE-2 |
| BE-4 | **QwenClient (PRIMARY)** ✨ | 🔴 HIGH | 6ч | Backend | BE-2, BE-3 |
| BE-4.5 | **T-ProClient (SECONDARY)** ✨ NEW | 🔴 HIGH | 5ч | Backend | BE-2, BE-3 |
| BE-5 | **LlamaClient (FALLBACK)** ✨ NEW | 🔴 HIGH | 6ч | Backend | BE-2, BE-3 |
| BE-6 | Docker + Docker Compose | 🟡 MED | 4ч | Backend | BE-1 |
| FE-1 | Vue 3 + Vite инициализация | 🔴 HIGH | 2ч | Frontend | BE-1 |
| FE-2 | Layout + навигация | 🟡 MED | 4ч | Frontend | FE-1 |
| FE-3 | API сервис + mock данные | 🟡 MED | 5ч | Frontend | FE-1 |
| FE-4 | Dashboard страница | 🟡 MED | 6ч | Frontend | FE-2, FE-3 |
| FE-5 | Optimize форма | 🟡 MED | 5ч | Frontend | FE-2, FE-3 |
| ML-1 | **ML окружение (Qwen/T-Pro/Llama)** | 🔴 HIGH | 3ч | ML | BE-1, BE-2 |
| ML-2 | **Benchmark для 3 НОВЫХ моделей** | 🟡 MED | 6ч | ML | ML-1, BE-3 |
| ML-3 | **Анализ + рекомендации (новые модели)** | 🟡 MED | 4ч | ML | ML-2 |
| QA-1 | **Test Plan + CI (для 3 новых моделей)** | 🟡 MED | 8ч | QA/PM | BE-1 |
| | | | | | |
| | **ИТОГО** | | **72 часа** | | |

## ⚠️ РИСКИ И MITIGATION

| Риск | Вероятность | Mitigation |
|------|-------------|-----------| 
| Qwen токен недоступен в Day 1 | Средняя | Используй mock, продолжай с T-Pro/Llama |
| Не все 3 модели доступны одновременно | Средняя | Prioritize: Qwen first, T-Pro second, Llama last |
| Backend разработчик застревает на LLM интеграции | Средняя | Pair programming с ML разработчиком |
| Недостаточно времени на Docker | Низкая | Docker может быть в Неделе 2 если нужно |
| Frontend разработчик ждёт API спецификации | Низкая | API контракт уже написан в docs/ |
| Llama модель слишком большая для локальной установки | Низкая | Используй облачный endpoint вместо локального |