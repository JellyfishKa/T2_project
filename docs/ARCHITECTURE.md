# АРХИТЕКТУРА И ТЕХНИЧЕСКИЙ ДИЗАЙН

**Архитектура системы, потоки данных и технические решения**

---

## Обзор архитектуры

```
┌─────────────────────────────────────────────┐
│      Frontend (Vue 3 + TypeScript)          │
│  - Dashboard, Формы, Визуализация маршрутов│
└──────────────────┬──────────────────────────┘
                   │
                   ↓ (HTTP/REST)
┌─────────────────────────────────────────────┐
│      Backend API (FastAPI + Python)         │
│  - LLM клиенты, Оптимизация маршрутов, Cache│
└───────┬─────────────────┬────────────────────┘
        │                 │
        ↓                 ↓
    ┌───────────┐    ┌──────────────┐
    │   LLM     │    │   Database   │
    │  Models   │    │ (PostgreSQL) │
    │           │    │              │
    │ GigaChat  │    │ Маршруты     │
    │ Cotype    │    │ Метрики      │
    │ T-Pro     │    │ Cache        │
    └───────────┘    └──────────────┘
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
class GigaChatClient(LLMClient):
    # Основная модель (Российская LLM)
    
class CotypeClient(LLMClient):
    # Fallback модель (локальная, всегда доступна)
    
class TProClient(LLMClient):
    # Альтернативная модель
```

**Стратегия fallback**:
```
Пробуем GigaChat
  ↓ (если fail)
Пробуем Cotype
  ↓ (если fail)
Пробуем T-Pro
  ↓ (если все fail)
Возвращаем ошибку
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
POST /api/v1/optimize
├── Вход: List[Location], ограничения
├── Процесс: LLMClient генерирует маршруты → алгоритм оптимизирует
└── Выход: OptimizedRoute (последовательность, время, стоимость)

GET /api/v1/metrics
├── Вход: route_id
├── Процесс: Fetch из DB + cache
└── Выход: PerformanceMetrics

POST /api/v1/benchmark
├── Вход: model_name, test_data
├── Процесс: Запустить бенчмарк
└── Выход: BenchmarkResult

GET /api/v1/health
├── Выход: HealthStatus (все сервисы работают?)
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
    optimized_sequence VARCHAR(255),  -- BE-1, BE-2, ...
    total_distance FLOAT,
    total_time INTEGER,  -- секунды
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Метрики
CREATE TABLE metrics (
    id UUID PRIMARY KEY,
    route_id UUID REFERENCES routes(id),
    model VARCHAR(50),  -- gigachat, cotype, tpro
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
├── Header (лого, навигация)
├── Dashboard.vue
│   ├── RouteMap.vue (визуализация)
│   ├── MetricsPanel.vue (статистика)
│   └── ResultsTable.vue (детали)
├── OptimizeView.vue
│   ├── OptimizationForm.vue (входы)
│   ├── ConstraintsPanel.vue (опции)
│   └── ProgressBar.vue (loading)
└── AnalyticsView.vue
    ├── PerformanceChart.vue
    ├── ComparisonTable.vue
    └── ExportButton.vue
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

// Mock interceptor (Неделя 1)
api.interceptors.response.use((config) => {
    if (process.env.NODE_ENV === 'development') {
        // Возвращаем mock данные
    }
});

// Реальные данные (Неделя 2)
// Удаляем mock interceptor, используем реальный backend
```

---

## Потоки данных

### Поток оптимизации маршрутов

```
Вход пользователя (магазины, ограничения)
    ↓
Frontend валидирует
    ↓
POST /api/v1/optimize
    ↓
Backend LLMClient.generate_route()
    ↓
GigaChat (попытка 1)
    ↓ (fail? → Cotype)
    ↓ (fail? → T-Pro)
    ↓
Алгоритмическая оптимизация
    ↓
Сохранить в базу
    ↓
Возвращаем optimized_sequence
    ↓
Frontend визуализирует на карте
    ↓
Отображаем метрики + сбережения
```

### Агрегация метрик

```
ML бенчмарки (Неделя 1)
    ↓
Запустить все 3 модели на test данных
    ↓
Измеряем: response_time, quality, cost
    ↓
Сохранить в базу
    ↓
Dashboard отображает сравнение
    ↓
Рекомендация: какую модель использовать
```

---

## Конфигурация

### Переменные окружения

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost/t2_db

# LLM Models
GIGACHAT_TOKEN=xxx
GIGACHAT_API_URL=https://api.gigachat.ru
COTYPE_MODEL_PATH=/models/cotype
TPRO_API_KEY=xxx

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
    'gigachat': os.getenv('ENABLE_GIGACHAT') == 'true',
    'cotype': True,  # Всегда включена (локальная)
    'tpro': os.getenv('ENABLE_TPRO') == 'true'
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
def test_gigachat_client():
    client = GigaChatClient()
    result = await client.generate_route([...])
    assert result.status == 'success'

def test_fallback():
    # Mock GigaChat fail
    # Должен fallback на Cotype
    result = await service.generate_route([...])
    assert result.model_used == 'cotype'

# test_api.py
def test_optimize_endpoint():
    response = client.post('/api/v1/optimize', {...})
    assert response.status_code == 200

def test_error_handling():
    response = client.post('/api/v1/optimize', {invalid})
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
      - GIGACHAT_TOKEN=...
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
- API key rotation (LLM tokens)

### Data Protection

- Database encryption (TLS)
- Secrets management (.env, не в repo)
- HTTPS only (production)
- Sanitized logs (без API ключей)

### Model Access

- GigaChat token IP restrictions (если доступно)
- Cotype локальная (без external доступа)
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
- GigaChat: ~1.5 сек (если доступна)
- Cotype: ~0.5 сек (локальная)
- T-Pro: ~1.2 сек (estimate)

---

## Технологические выборы & почему

| Выбор | Почему |
|-------|--------|
| FastAPI | Современный, async, auto-documentation, отлично для ML |
| Vue 3 | Легковесный, простая кривая обучения, отлично для dashboards |
| PostgreSQL | Надёжная, mature, хорошо для structured данных |
| Redis | Быстрый caching, pub/sub для real-time updates |
| Docker | Консистентное окружение, простой deployment |
| Pydantic | Type safety, валидация, сериализация |
| SQLAlchemy | ORM, migrations, relationships |
| Pytest | Python стандарт, отличные fixtures, mocking |
| TypeScript | Type safety, лучше IDE поддержка |

---

**Вопросы?** Посмотри специфичные файлы реализации в `/backend`, `/frontend`, `/ml`
