# АРХИТЕКТУРА И ТЕХНИЧЕСКИЙ ДИЗАЙН

**Архитектура системы, потоки данных и технические решения**

---

## Обзор архитектуры

```
+---------------------------------------------+
|      Frontend (Vue 3 + TypeScript)          |
|  - Dashboard, Формы, Визуализация маршрутов |
+----------------------+----------------------+
                       |
                       v (HTTP/REST)
+---------------------------------------------+
|      Backend API (FastAPI + Python)         |
|  - LLM клиенты, Оптимизация маршрутов, Cache|
+---------+-----------------+-----------------+
          |                 |
          v                 v
    +-----------+    +--------------+
    |   LLM     |    |   Database   |
    |  Models   |    | (PostgreSQL) |
    |           |    |              |
    | Qwen      |    | Маршруты     |
    | Llama     |    | Метрики      |
    |           |    | Cache        |
    +-----------+    +--------------+
```

---

## Основные компоненты

### 1. Интерфейс LLM клиента

**Design Pattern**: Strategy + Adapter

```python
# Базовый интерфейс
class LLMClient(ABC):
    @abstractmethod
    async def generate_route(routes: List[Location]) -> str

    @abstractmethod
    async def analyze_metrics(data: Dict) -> str

# Реализации
class QwenClient(LLMClient):
    # Основная модель (лучшее качество)

class LlamaClient(LLMClient):
    # Fallback модель (максимальная надежность, open-source)
```

**Стратегия fallback**:
```
Пробуем Qwen (Primary)
  | (если fail)
Пробуем Llama (Fallback)
  | (если все fail)
Greedy Algorithm (всегда работает)
```

**Почему такой дизайн**:
- Развязанные реализации (легко добавить новые модели)
- Автоматический fallback (без ручного вмешательства)
- Тестируемый (mock каждый клиент отдельно)
- Расширяемый (добавь новые модели без изменения core)

---

### 2. API маршруты

**Структура endpoints**:

```
POST /qwen/optimize
|-- Вход: List[Location], ограничения
|-- Процесс: QwenClient генерирует маршруты
|-- Выход: OptimizedRoute (последовательность, время, стоимость)

POST /llama/optimize
|-- Вход: List[Location], ограничения
|-- Процесс: LlamaClient генерирует маршруты
|-- Выход: OptimizedRoute

GET /health
|-- Выход: HealthStatus (все сервисы работают?)
```

**Обработка ошибок**:
```
200 OK: Успех
400 Bad Request: Некорректный вход
500 Internal Error: Backend ошибка
503 Service Unavailable: Все модели недоступны
```

---

### 3. Схема базы данных

**Ключевые сущности**:

```sql
-- Маршруты
CREATE TABLE routes (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    locations JSONB,  -- List of store locations
    optimized_sequence VARCHAR(255),
    total_distance FLOAT,
    total_time INTEGER,  -- секунды
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Метрики
CREATE TABLE metrics (
    id UUID PRIMARY KEY,
    route_id UUID REFERENCES routes(id),
    model VARCHAR(50),  -- qwen, llama, greedy
    response_time_ms INTEGER,
    quality_score FLOAT,  -- 0-100
    cost FLOAT,  -- стоимость модели
    timestamp TIMESTAMP
);

-- Cache
CREATE TABLE cache (
    key VARCHAR(255) PRIMARY KEY,
    value JSONB,
    expires_at TIMESTAMP
);
```

---

### 4. Архитектура Frontend

**Иерархия компонентов**:

```
App.vue
|-- Header (лого, навигация)
|-- Dashboard.vue
|   |-- RouteMap.vue (визуализация)
|   |-- MetricsPanel.vue (статистика)
|   |-- ResultsTable.vue (детали)
|-- OptimizeView.vue
|   |-- OptimizationForm.vue (входы)
|   |-- ConstraintsPanel.vue (опции)
|   |-- ProgressBar.vue (loading)
|-- AnalyticsView.vue
    |-- PerformanceChart.vue
    |-- ComparisonTable.vue
    |-- ExportButton.vue
```

**Управление состоянием**:
- Используй Pinia для глобального состояния
- Store: маршруты, метрики, UI состояние
- Actions: fetchRoutes, optimizeRoute, benchmarkModels

**API коммуникация**:
```typescript
// api.ts
export const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL,
    timeout: 30000
});
```

---

## Потоки данных

### Поток оптимизации маршрутов

```
Вход пользователя (магазины, ограничения)
    |
Frontend валидирует
    |
POST /qwen/optimize (или /llama/optimize)
    |
Backend LLMClient.generate_route()
    |
Qwen (попытка 1)
    | (fail? -> Llama)
    | (fail? -> Greedy)
    |
Алгоритмическая оптимизация
    |
Сохранить в базу
    |
Возвращаем optimized_sequence + model_used
    |
Frontend визуализирует на карте
    |
Отображаем метрики + сбережения
```

### Агрегация метрик

```
ML бенчмарки
    |
Запустить все 2 модели на test данных
    |
Измеряем: response_time, quality, cost
    |
Сохранить в базу
    |
Dashboard отображает сравнение
    |
Рекомендация: какую модель использовать
```

---

## Конфигурация

### Переменные окружения

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost/t2_db

# LLM Models
QWEN_API_ENDPOINT=local
QWEN_MODEL_ID=qwen2-0_5b-instruct-q4_k_m.gguf

LLAMA_API_ENDPOINT=local
LLAMA_MODEL_ID=Llama-3.2-1B-Instruct-Q4_K_M.gguf

HF_TOKEN=your_hf_token

# Cache
REDIS_URL=redis://localhost:6379

# API
API_PORT=8000
DEBUG=false

# Frontend
VITE_API_URL=http://localhost:8000
```

### Feature flags

```python
# Включить/отключить модели во время выполнения
ENABLED_MODELS = {
    'qwen': os.getenv('ENABLE_QWEN', 'true') == 'true',
    'llama': True,  # Всегда включена (локальная, fallback)
}

# Cache настройки
CACHE_TTL = int(os.getenv('CACHE_TTL', 3600))
USE_CACHE = os.getenv('USE_CACHE') == 'true'
```

---

## Стратегия тестирования

### Backend тесты

```python
# test_llm_clients.py
def test_qwen_client():
    client = QwenClient()
    result = await client.generate_route([...])
    assert result.status == 'success'

def test_fallback():
    # Mock Qwen fail
    # Должен fallback на Llama
    result = await service.generate_route([...])
    assert result.model_used == 'llama'

# test_api.py
def test_optimize_endpoint():
    response = client.post('/qwen/optimize', {...})
    assert response.status_code == 200

def test_error_handling():
    response = client.post('/qwen/optimize', {invalid})
    assert response.status_code == 400
```

### Frontend тесты

```typescript
// Dashboard.spec.ts
describe('Dashboard', () => {
    it('отображает метрики маршрута', () => {
        // Mount component
        // Check метрики отображены
    });

    it('визуализирует маршрут на карте', () => {
        // Mount RouteMap
        // Check маркеры отрендерены
    });
});
```

---

## Архитектура деплоя

### Docker настройка

```yaml
version: '3.9'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://...
      - QWEN_MODEL_ID=...
      - LLAMA_MODEL_ID=...
      - HF_TOKEN=...
    depends_on:
      - db
      - redis

  frontend:
    build: ./frontend
    ports:
      - "80:5173"
    environment:
      - VITE_API_URL=http://backend:8000

  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD=...

  redis:
    image: redis:7
    ports:
      - "6379:6379"
```

### Производство considerations

- Docker multi-stage builds (оптимизировать размер image)
- Environment variable injection (управление secrets)
- Database migrations (Alembic)
- Health checks (все endpoints)
- Логирование aggregation (CloudWatch/ELK)
- Мониторинг (Prometheus, Grafana)

---

## Безопасность considerations

### API Security

- Input validation (Pydantic)
- Rate limiting (FastAPI middleware)
- CORS configuration (только frontend)
- Аутентификация (basic для Недели 1, JWT для prod)
- API key rotation (HF tokens)

### Data Protection

- Database encryption (TLS)
- Secrets management (.env, не в repo)
- HTTPS only (production)
- Sanitized logs (без API ключей)

### Model Access

- Hugging Face token IP restrictions (если доступно)
- Llama локальная (без external доступа)
- Rate limiting per модель
- Cost monitoring

---

## Целевые показатели производительности

### Backend
- API response time: <2 сек (p99)
- Optimization task: <5 сек
- Database queries: <100ms

### Frontend
- Page load: <3 сек
- Route visualization: <1 сек
- Dashboard interaction: <200ms

### LLM Models
- Qwen: ~3-10 сек (лучшее качество, основная)
- Llama: ~5-15 сек (надежный fallback)

---

## Технологические выборы & почему

| Выбор | Почему |
|-------|--------|
| FastAPI | Современный, async, auto-documentation, отлично для ML |
| Vue 3 | Легковесный, простая кривая обучения, отлично для dashboards |
| PostgreSQL | Надежная, mature, хорошо для structured данных |
| Redis | Быстрый caching, pub/sub для real-time updates |
| Docker | Консистентное окружение, простой deployment |
| Pydantic | Type safety, валидация, сериализация |
| SQLAlchemy | ORM, migrations, relationships |
| Pytest | Python стандарт, отличные fixtures, mocking |
| TypeScript | Type safety, лучше IDE поддержка |
| llama-cpp-python | Единый интерфейс для всех GGUF моделей |

---

**Вопросы?** Посмотри специфичные файлы реализации в `/backend`, `/frontend`, `/ml`
