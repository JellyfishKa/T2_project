# КОНТРАКТ API

**Соглашение Frontend-Backend по структуре API**

---

## Обзор

Этот документ определяет контракт между Frontend и Backend.
**Frontend использует это для создания mock interceptors.**
**Backend реализует ровно это.**

**Ключевой принцип**: Сначала согласовываем интерфейс, потом реализуем.

---

## Базовый URL

```
Разработка: http://localhost:8000/api/v1
Production: https://api.t2-retail.com/api/v1
```

---

## Основные модели данных

### Location (Локация)
```json
{
  "id": "store-123",
  "name": "Магазин в Москве",
  "latitude": 55.7558,
  "longitude": 37.6173,
  "address": "Москва, Россия",
  "time_window_start": "09:00",
  "time_window_end": "18:00",
  "priority": 1
}
```

### Route (Маршрут)
```json
{
  "id": "route-456",
  "name": "Маршрут 1 - День 1",
  "locations": ["store-1", "store-2", "store-3"],
  "total_distance_km": 45.3,
  "total_time_hours": 2.5,
  "total_cost_rub": 1500,
  "model_used": "qwen",
  "fallback_reason": null,
  "created_at": "2026-01-06T10:30:00Z"
}
```

### Metric (Метрика)
```json
{
  "id": "metric-789",
  "route_id": "route-456",
  "model": "qwen",
  "response_time_ms": 1250,
  "quality_score": 0.85,
  "cost_rub": 25.50,
  "timestamp": "2026-01-06T10:30:00Z"
}
```

### BenchmarkResult (Результат бенчмарка)
```json
{
  "model": "qwen",
  "num_tests": 10,
  "avg_response_time_ms": 1250,
  "min_response_time_ms": 850,
  "max_response_time_ms": 2100,
  "avg_quality_score": 0.87,
  "total_cost_rub": 250.00,
  "success_rate": 1.0,
  "timestamp": "2026-01-06T11:00:00Z"
}
```

---

## Endpoints

### 1. POST /optimize

**Генерировать оптимизированный маршрут**

```
Запрос:
POST /optimize
Content-Type: application/json

{
  "locations": [
    {
      "id": "store-1",
      "name": "Магазин 1",
      "latitude": 55.7558,
      "longitude": 37.6173,
      "time_window_start": "09:00",
      "time_window_end": "18:00"
    },
    {
      "id": "store-2",
      "name": "Магазин 2",
      "latitude": 55.7489,
      "longitude": 37.6160,
      "time_window_start": "09:00",
      "time_window_end": "18:00"
    }
  ],
  "constraints": {
    "vehicle_capacity": 100,
    "max_distance_km": 500,
    "start_time": "09:00",
    "end_time": "18:00"
  },
  "preferred_model": "qwen"
}

Ответ 200 OK:
{
  "route_id": "route-456",
  "locations_sequence": ["store-1", "store-2"],
  "total_distance_km": 5.5,
  "total_time_hours": 0.5,
  "total_cost_rub": 500,
  "model_used": "qwen",
  "fallback_reason": null,
  "created_at": "2026-01-06T10:30:00Z"
}

Ответ 400 Bad Request:
{
  "error": "Неправильные локации",
  "details": "location не имеет 'name'"
}

Ответ 503 Service Unavailable:
{
  "error": "Все модели недоступны",
  "details": "Qwen down, Llama down"
}
```

---

### 2. GET /routes

**Получить список всех маршрутов**

```
Запрос:
GET /routes?skip=0&limit=10

Ответ 200 OK:
{
  "total": 42,
  "items": [
    {
      "id": "route-456",
      "name": "Маршрут 1",
      "total_distance_km": 45.3,
      "total_time_hours": 2.5,
      "total_cost_rub": 1500,
      "model_used": "qwen",
      "created_at": "2026-01-06T10:30:00Z"
    },
    ...
  ]
}
```

---

### 3. GET /routes/{route_id}

**Получить детали конкретного маршрута**

```
Запрос:
GET /routes/route-456

Ответ 200 OK:
{
  "id": "route-456",
  "name": "Маршрут 1",
  "locations": [
    {
      "id": "store-1",
      "name": "Магазин 1",
      "latitude": 55.7558,
      "longitude": 37.6173
    },
    ...
  ],
  "locations_sequence": ["store-1", "store-2"],
  "total_distance_km": 45.3,
  "total_time_hours": 2.5,
  "total_cost_rub": 1500,
  "model_used": "qwen",
  "fallback_reason": null,
  "created_at": "2026-01-06T10:30:00Z"
}

Ответ 404 Not Found:
{
  "error": "Маршрут не найден",
  "route_id": "route-456"
}
```

---

### 4. GET /metrics

**Получить метрики маршрута**

```
Запрос:
GET /metrics?route_id=route-456

Ответ 200 OK:
{
  "route_id": "route-456",
  "metrics": [
    {
      "model": "qwen",
      "response_time_ms": 2345,
      "quality_score": 0.92,
      "cost_rub": 0.00,
      "timestamp": "2026-01-06T10:30:00Z"
    },
    {
      "model": "llama",
      "response_time_ms": 4500,
      "quality_score": 0.85,
      "cost_rub": 0.00,
      "timestamp": "2026-01-06T10:30:00Z"
    }
  ]
}
```

---

### 5. POST /benchmark

**Запустить бенчмарк на всех моделях**

```
Запрос:
POST /benchmark
Content-Type: application/json

{
  "test_locations": [
    { "id": "store-1", "name": "Магазин 1", "latitude": 55.7558, "longitude": 37.6173 },
    { "id": "store-2", "name": "Магазин 2", "latitude": 55.7489, "longitude": 37.6160 },
    ...
  ],
  "num_iterations": 5
}

Ответ 200 OK:
{
  "total_duration_seconds": 45.2,
  "results": [
    {
      "model": "qwen",
      "num_tests": 5,
      "avg_response_time_ms": 2345,
      "min_response_time_ms": 1850,
      "max_response_time_ms": 3100,
      "avg_quality_score": 0.92,
      "total_cost_rub": 0.00,
      "success_rate": 1.0
    },
    {
      "model": "llama",
      "num_tests": 5,
      "avg_response_time_ms": 4500,
      "min_response_time_ms": 3500,
      "max_response_time_ms": 6000,
      "avg_quality_score": 0.85,
      "total_cost_rub": 0.00,
      "success_rate": 1.0
    }
  ]
}

Ответ 202 Accepted (если async):
{
  "benchmark_id": "bench-123",
  "status": "in_progress",
  "estimated_completion": "2026-01-06T11:15:00Z"
}
```

---

### 6. GET /benchmark/{benchmark_id}

**Получить статус/результаты бенчмарка**

```
Запрос:
GET /benchmark/bench-123

Ответ 200 OK:
{
  "benchmark_id": "bench-123",
  "status": "completed",
  "results": [...]
}

Ответ 202 Accepted:
{
  "status": "in_progress",
  "progress_percent": 60
}
```

---

### 7. GET /health

**Health check**

```
Запрос:
GET /health

Ответ 200 OK:
{
  "status": "healthy",
  "services": {
    "database": "connected",
    "qwen": "available",
    "llama": "available"
  }
}

Ответ 503 Service Unavailable:
{
  "status": "unhealthy",
  "services": {
    "database": "disconnected",
    "qwen": "unavailable",
    "llama": "available"
  }
}
```

---

## Model-specific endpoints

Помимо общего `/optimize`, каждая модель имеет отдельный endpoint:

| Endpoint | Модель | Описание |
|----------|--------|----------|
| POST /qwen/optimize | Qwen | Прямой вызов Qwen (Primary) |
| POST /llama/optimize | Llama | Прямой вызов Llama (Fallback) |

Формат запроса и ответа аналогичен `/optimize`, но без fallback.

---

## Ответы об ошибках

Все ошибки следуют этому формату:

```json
{
  "error": "Название ошибки",
  "message": "Подробное сообщение об ошибке",
  "code": "ERROR_CODE",
  "details": {}
}
```

### Коды статуса

| Код | Значение | Пример |
|-----|----------|--------|
| 200 | Успех | Маршрут оптимизирован |
| 201 | Создано | Новый ресурс создан |
| 400 | Bad Request | Неправильные входные данные |
| 404 | Not Found | Маршрут не существует |
| 429 | Too Many Requests | Rate limited |
| 500 | Internal Error | Backend ошибка |
| 503 | Service Unavailable | Все модели недоступны |

---

## Стратегия mock данных

**Frontend подход Неделя 1**:

```typescript
// mock-interceptor.ts
import axios from 'axios';

const MOCK_ROUTES = [
  {
    id: 'route-456',
    name: 'Маршрут 1',
    locations: [...],
    total_distance_km: 45.3,
    model_used: 'qwen',
    // ... и т.д
  }
];

// Intercept все запросы
api.interceptors.response.use((config) => {
  if (isDevelopment()) {
    const endpoint = config.url;

    if (endpoint.includes('/optimize')) {
      return { data: generateMockRoute() };
    }
    if (endpoint.includes('/routes')) {
      return { data: { items: MOCK_ROUTES } };
    }
    if (endpoint.includes('/health')) {
      return { data: { status: 'healthy' } };
    }
  }
  return config;
});

// Удали это в Неделе 2 когда backend готов
```

---

## API контракт чек-лист

**Для Backend**:
- [ ] Реализовать все 7 endpoints
- [ ] Реализовать model-specific endpoints (/qwen, /llama)
- [ ] Возвращать точные модели данных
- [ ] Обрабатывать все error case
- [ ] Response times <2 сек
- [ ] Коды статуса корректны

**Для Frontend**:
- [ ] Использовать mock interceptor Неделя 1
- [ ] Использовать реальный API Неделя 2
- [ ] Обработка ошибок для каждого endpoint
- [ ] Loading states для async операций
- [ ] Валидация перед отправкой

---

## Версионирование

- **Текущая версия**: v1
- **URL pattern**: `/api/v1/...`
- **Будущее**: v2, v3 могут существовать одновременно

---

## Заметки для реализации

1. **Timestamps**: Всегда ISO 8601 формат (`2026-01-06T10:30:00Z`)
2. **Координаты**: Latitude/longitude (не отдельно)
3. **Стоимость**: В Рублях (RUB), 2 decimal places
4. **Расстояния**: В километрах
5. **Время**: В HH:MM формате или часах (зависит от endpoint)
6. **IDs**: UUIDs или простые строки (консистентность важна)
7. **model_used**: Одно из: `"qwen"`, `"llama"`
8. **fallback_reason**: `null` если основная модель справилась, строка с причиной если был fallback
