# 📋 НЕДЕЛЯ 2 - ОБНОВЛЕННЫЕ ТАСКИ (NEW LLM: Qwen, T-Pro, Llama)

## 🔄 ОБНОВЛЕНИЕ: NEW LLM MODELS IN WEEK 2

**Было (Old)**:
```
GigaChat (основная)
Cotype (fallback)
T-Pro (вторая)
```

**Стало (New - после Week 1)**:
```
Qwen (Primary) - will be tested
T-Pro (Secondary) - will be tested
Llama (Fallback) - will be tested
```

---

## 📊 ОБЗОР НЕДЕЛИ 2

**Цель**: MVP feature complete — все основные функции работают с НОВЫМИ LLM моделями

**Velocity**: 14-18 задач на неделю (в неделе 5 дней)

**Распределение**:
- Backend: 7 задач (MVP endpoints)
- Frontend: 6 задач (interactive UI)
- ML: 3 задачи (optimization + integration)
- QA/PM: 2 задачи (testing + stakeholder management)

**Status**: Переход из Week 1 → реальные API вызовы с Qwen/T-Pro/Llama, integration тестирование

---

## ⚡ ПРЕДВАРИТЕЛЬНЫЕ УСЛОВИЯ (Week 1 DONE)

**Backend** ✅:
- ✅ **Qwen** Client работает (новое)
- ✅ **T-Pro** Client работает (новое)
- ✅ **Llama** Client работает (новое)
- ✅ Docker setup готов
- ✅ PostgreSQL доступна
- ✅ LLM fallback механизм готов (Qwen → T-Pro → Llama)

**Frontend** ✅:
- ✅ Vue 3 проект работает
- ✅ Mock API работает
- ✅ Layout + основные компоненты созданы

**ML** ✅:
- ✅ Benchmark скрипт готов (для 3 новых моделей)
- ✅ Рекомендация primary/fallback модели определена

---

## ✅ BACKEND ТАСКИ (7 задач) - ОБНОВЛЕНО ДЛЯ НОВЫХ LLM

### BE-8: Создание Database schema для маршрутов и магазинов

**Приоритет**: 🔴 HIGH

**Оценка**: 4 часа

**Assignee**: Backend разработчик

**Зависит от**: BE-6 (Docker + PostgreSQL ready)

**Описание**:
Создать SQL schema для хранения магазинов, маршрутов и метрик. Это фундамент для всех операций с данными в Week 2.

**Acceptance Criteria**:
- ✅ Файл backend/src/database/migrations/001_initial_schema.sql создан
- ✅ SQLAlchemy ORM модели созданы (Location, Route, Metric, OptimizationResult)
- ✅ Таблицы включают:
  - locations (id, name, lat, lon, time_window_start, time_window_end)
  - routes (id, name, locations_order, total_distance, total_time, total_cost)
  - metrics (id, route_id, model_name, response_time_ms, quality_score, cost)
    - **model_name поддерживает**: "Qwen", "T-Pro", "Llama"
  - optimization_results (id, original_route, optimized_route, improvement_percentage, model_used)
- ✅ Relationships настроены (foreign keys, cascades)
- ✅ Indices созданы для поиска (на id, route_id, model_name)
- ✅ Migration запускается успешно: `alembic upgrade head`
- ✅ Unit тесты для моделей написаны

**Model names в БД**:
```
'Qwen' → Alibaba Qwen (Primary)
'T-Pro' → T-Pro (Secondary)
'Llama' → Open-source Llama (Fallback)
```

---

### BE9: Создание API endpoint для загрузки магазинов (POST /locations/upload)

**Приоритет**: 🔴 HIGH

**Оценка**: 3 часа

**Описание**:
Создать FastAPI endpoint который принимает список магазинов и сохраняет их в БД. Это point 1 в workflow оптимизации.

**Acceptance Criteria**:
- ✅ Endpoint POST /api/v1/locations/upload создан
- ✅ Request body: JSON с array магазинов
- ✅ Response: список созданных locations с ID
- ✅ Валидация входных данных
- ✅ Error handling (duplicates, invalid data)
- ✅ Логирование (сколько locations загружено)
- ✅ Unit тесты (success, validation error, duplicate)

---

### BE-10: Реализация базового алгоритма оптимизации маршрутов

**Приоритет**: 🔴 HIGH

**Оценка**: 8 часов

**Assignee**: Backend разработчик

**Зависит от**: BE-8, BE-3, BE-4, BE-4.5, BE-5 **(ОБНОВЛЕНО - теперь 3 LLM clients)**

**Описание**:
Реализовать базовый алгоритм оптимизации маршрутов используя ВСЕ 3 НОВЫХ LLM модели (Qwen, T-Pro, Llama) и простой nearest-neighbor алгоритм. Это ядро MVP функциональности.

**Acceptance Criteria**:
- ✅ Файл backend/src/services/route_optimizer.py создан с классом RouteOptimizer
- ✅ Методы реализованы:
  - `async def optimize_route(locations: List[Location], preferred_model: str = None) -> OptimizedRoute`
  - `async def calculate_distance(lat1, lon1, lat2, lon2) -> float`
  - `async def use_llm_for_analysis(route: Route) -> str` (использует все 3 модели)
- ✅ Алгоритм:
  1. Начиная с depot (первая локация или центр)
  2. Nearest-neighbor: найди ближайший неvisited магазин
  3. Добавь в маршрут
  4. Повтори пока все не visited
  5. Используй LLM для проверки и улучшения (попробуй все 3 модели с fallback)
- ✅ Использование LLM моделей (НОВОЕ):
  - **Priority order**: Qwen (try first) → T-Pro (if Qwen fails) → Llama (if T-Pro fails) → error
  - Логируй какую модель используешь
  - Сохраняй в БД какая модель использовалась
  - Если `preferred_model` указана, начни с неё (потом fallback chain)
- ✅ Обработка constraints (same as before)
- ✅ Результат включает:
  - Optimized order of locations
  - Total distance, time, cost
  - **model_used**: какую модель использовали (Qwen/T-Pro/Llama)
  - LLM insights (опционально)
- ✅ Unit тесты (простой маршрут, constraints, fallback от Qwen к T-Pro, fallback к Llama)
- ✅ Response time документирован (goal: < 5 sec для 50 магазинов)

**Code example**:
```python
class RouteOptimizer:
    def __init__(self, qwen_client, tpro_client, llama_client):
        self.qwen = qwen_client
        self.tpro = tpro_client
        self.llama = llama_client
    
    async def optimize_route(self, locations, preferred_model=None):
        # Decide which model to use
        models_to_try = self._get_model_priority(preferred_model)
        # Try each model in priority order
        for model in models_to_try:
            try:
                result = await model.generate_route(locations)
                logger.info(f"Used model: {model.name}")
                result['model_used'] = model.name
                return result
            except Exception as e:
                logger.warning(f"Model {model.name} failed, trying next...")
                continue
        # All models failed
        raise Exception("All LLM models unavailable")
```

---

### BE-10: Создание API endpoint для оптимизации маршрутов (POST /optimize)

**Приоритет**: 🔴 HIGH

**Оценка**: 4 часа

**Описание**:
Создать FastAPI endpoint который принимает locations и возвращает оптимизированный маршрут. Это главный endpoint MVP.

**Acceptance Criteria**:
- ✅ Endpoint POST /api/v1/optimize создан
- ✅ Request body:
  ```json
  {
    "locations": [...],
    "constraints": {...},
    "preferred_model": "Qwen"  // опционально: Qwen, T-Pro, Llama
  }
  ```
- ✅ Response:
  ```json
  {
    "optimized_route": [...],
    "total_distance": 42.5,
    "total_time": 120,
    "total_cost": 850,
    "improvement_vs_original": "25%",
    "model_used": "Qwen",  // или "T-Pro", "Llama"
    "response_time_ms": 2345,
    "fallback_reason": null  // если используется fallback, указать почему
  }
  ```
- ✅ Асинхронная обработка (не блокирует)
- ✅ Fallback механизм (Qwen → T-Pro → Llama) ✅ **НОВОЕ**
- ✅ Логирование всех шагов (включая какая модель использовалась)
- ✅ Error handling (invalid constraints, too many locations)
- ✅ Unit тесты (success, fallback from Qwen to T-Pro, fallback to Llama, error cases)

**Response examples**:
```json
// Success with Qwen
{
  "model_used": "Qwen",
  "fallback_reason": null,
  "response_time_ms": 2345
}

// Fallback to T-Pro (Qwen was slow/unavailable)
{
  "model_used": "T-Pro",
  "fallback_reason": "Qwen timeout after 30 sec",
  "response_time_ms": 2100
}

// Fallback to Llama (T-Pro failed)
{
  "model_used": "Llama",
  "fallback_reason": "T-Pro auth error",
  "response_time_ms": 5000
}

// All models failed: error returned
{
  "error": "All LLM models unavailable",
  "fallback_reason": "All LLM models unavailable"
}
```

---

### BE-11: Создание API endpoint для получения метрик маршрута (GET /routes/{id}/metrics)

**Приоритет**: 🟡 MEDIUM

**Оценка**: 3 часа

**Описание**:
Создать endpoint который возвращает метрики конкретного маршрута (расстояние, время, стоимость, **какую модель использовали**).

**Acceptance Criteria**:
- ✅ Endpoint GET /api/v1/routes/{id}/metrics создан
- ✅ Response:
  ```json
  {
    "route_id": "uuid",
    "total_distance": 42.5,
    "total_time": 120,
    "total_cost": 850,
    "model_used": "Qwen",  // или "T-Pro", "Llama" - НОВОЕ
    "fallback_reason": null,  // если использовался fallback - НОВОЕ
    "response_time_ms": 2345,
    "quality_score": 92,
    "created_at": "2026-01-17T10:30:00Z"
  }
  ```
- ✅ Error handling (route not found → 404)
- ✅ Unit тесты

---

### BE-12: Интеграция LLM анализа в route optimization (опциональный insights)

**Приоритет**: 🟡 MEDIUM

**Оценка**: 5 часов

**Описание**:
Добавить опциональный LLM анализ каждого оптимизированного маршрута для генерации insights, **используя все 3 новых модели (Qwen, T-Pro, Llama)**.

**Acceptance Criteria**:
- ✅ После оптимизации, LLM анализирует результат:
  - Insights примеры (same as before)
- ✅ Insights добавляются в response (опциональное поле)
- ✅ **Используются все 3 новых модели** (не только основная):
  - Попробуй Qwen первой для insights
  - Если Qwen не доступна → T-Pro
  - Если T-Pro не доступна → Llama
  - Никогда не fail (даже без insights это OK)
- ✅ Insights кэшируются (не вызывай LLM дважды для одного маршрута)
- ✅ Unit тесты (fallback chain для insights)

---

### BE-13: API endpoint для сравнения моделей (GET /benchmark/compare)

**Приоритет**: 🟡 MEDIUM

**Оценка**: 4 часа

**Описание**:
Создать endpoint который возвращает сравнение performance **ВСЕХ 3 НОВЫХ МОДЕЛЕЙ** (Qwen, T-Pro, Llama) на одном маршруте. Frontend будет использовать для dashboard.

**Acceptance Criteria**:
- ✅ Endpoint GET /api/v1/benchmark/compare?route_id=uuid создан
- ✅ Response:
  ```json
  {
    "route_id": "uuid",
    "comparisons": [
      {
        "model": "Qwen",
        "response_time_ms": 2345,
        "quality_score": 92,
        "cost_rub": 45,  // cost if paid API
        "status": "success"
      },
      {
        "model": "T-Pro",
        "response_time_ms": 1800,  // faster than Qwen
        "quality_score": 88,
        "cost_rub": 60,
        "status": "success"
      },
      {
        "model": "Llama",
        "response_time_ms": 4500,  // slowest but reliable
        "quality_score": 85,
        "cost_rub": 0,  // local, free
        "status": "success"
      },
    ]
  }
  ```
- ✅ Если route не был проанализирован всеми моделями → run benchmark сейчас
- ✅ Результаты кэшируются (TTL 1 час)
- ✅ Unit тесты

**Model comparison table**:
```
| Model | Speed | Quality | Cost | Reliability |
|-------|-------|---------|------|-------------|
| Qwen | Medium (2.3s) | High (92) | $0.45 | Good |
| T-Pro | Fast (1.8s) | Medium (88) | $0.60 | Better |
| Llama | Slow (4.5s) | Medium (85) | $0 | Best |
```

---

## 🎨 FRONTEND ТАСКИ (6 задач) - Same as before

*(FE-6 to FE-10 остаются без изменений, но будут работать с НОВЫМИ моделями)*

### FE-6, FE-7, FE-8, FE-9, FE-10

**Key updates**:
- Model names shown in UI: "Qwen", "T-Pro", "Llama" вместо "GigaChat", "Cotype", "T-Pro"
- Dashboard будет сравнивать все 3 модели (instead of 3 old models)
- Analytics будут показывать новые модели
- Model selector в frontend будет соответствовать новым моделям

---

## 🤖 ML ТАСКИ (3 задачи) - ОБНОВЛЕНО ДЛЯ НОВЫХ LLM

### ML-4: Оценка качества оптимизации (базовая метрика)

**Приоритет**: 🔴 HIGH

**Оценка**: 4 часа

**Описание**:
Создать функцию для оценки качества оптимизированного маршрута в сравнении с базовым маршрутом. **Должна работать со ВСЕМИ 3 моделями (Qwen, T-Pro, Llama)**.

**Acceptance Criteria**: (same as before, but models updated)

---

### ML-5: Сравнение результатов 3 НОВЫХ моделей на один маршрут

**Приоритет**: 🟡 MEDIUM

**Оценка**: 6 часов

**Описание**:
Обновить benchmark скрипт для сравнения результатов оптимизации **ВСЕХ 3 НОВЫХ МОДЕЛЕЙ** (Qwen, T-Pro, Llama) на один маршрут в real-time.

**Acceptance Criteria**:
- ✅ Скрипт ml/benchmarks/optimization_comparison.py создан
- ✅ Функция: `def compare_models_optimization(test_locations) -> ComparisonResults`
- ✅ **Для каждой из 3 моделей** (Qwen, T-Pro, Llama):
  - Запустить оптимизацию
  - Собрать результаты (маршрут, расстояние, время, стоимость)
  - Оценить качество (используя ML-4)
  - Записать response time
  - Записать любые ошибки
  - **Запиши fallback reason если была цепочка fallback**
- ✅ Baseline для сравнения
- ✅ Результаты сохранить в JSON: ml/benchmarks/optimization_results.json
- ✅ Генерируй отчёт: ml/benchmarks/optimization_report.md с таблицей сравнения
- ✅ Unit тесты

**Benchmark report example**:
```markdown
# Benchmark Report: Optimization Quality

## Test Date: 2026-01-17
## Test Case: 50 random locations in Moscow

### Results:

| Model | Distance (km) | Time (min) | Quality Score | Response Time | Cost |
|-------|---------------|-----------|---------------|----------------|------|
| Qwen | 42.5 | 120 | 92 | 2345ms | $0.45 |
| T-Pro | 44.2 | 125 | 88 | 1800ms | $0.60 |
| Llama | 45.1 | 130 | 85 | 4500ms | $0.00 |

### Findings:
- Qwen best quality (92)
- T-Pro fastest (1800ms)
- Llama most reliable
```

---

### ML-6: Создание рекомендаций для выбора модели (best model selector)

**Приоритет**: 🟡 MEDIUM

**Оценка**: 4 часа

**Описание**:
Создать logic для рекомендации **какую из 3 НОВЫХ МОДЕЛЕЙ** (Qwen, T-Pro, Llama) использовать в зависимости от constraints и данных.

**Acceptance Criteria**:
- ✅ Файл backend/src/services/model_selector.py создан
- ✅ Функция: `def select_best_model(num_locations: int, time_constraint: str) -> str`
- ✅ **Логика для НОВЫХ МОДЕЛЕЙ**:
  - Если < 20 магазинов и быстрый ответ нужен → **T-Pro** (fastest, good quality)
  - Если 20-100 магазинов и качество важно → **Qwen** (best quality)
  - Если > 100 магазинов → попробуй **T-Pro** (faster than Qwen)
  - Если strict reliability requirement → **Llama** (most reliable)
  - Если модель не доступна → fallback chain
- ✅ Документирована в docstring с примерами
- ✅ Unit тесты (разные сценарии с новыми моделями)
- ✅ Рекомендация включается в API response (optional field "recommended_model")

**Selection logic**:
```python
def select_best_model(num_locations, time_constraint):
    if time_constraint == "urgent":
        return "T-Pro"  # Fastest
    elif num_locations < 50:
        return "Qwen"  # Best quality for small sets
    elif num_locations >= 50 and num_locations < 200:
        return "T-Pro"  # Good balance
    else:  # num_locations >= 200
        return "Llama"  # Most reliable for large sets
```

---

## 📊 QA/PM ТАСКИ (2 задачи) - ОБНОВЛЕНО

### QA-2: Integration testing — Backend + Frontend + NEW LLM Models

**Приоритет**: 🔴 HIGH

**Оценка**: 8 часов

**Описание**:
Создать integration тесты для всей системы с НОВЫМИ 3 LLM моделями (Qwen, T-Pro, Llama).

**Acceptance Criteria**:
- ✅ Файл tests/integration/test_end_to_end.py создан
- ✅ Test cases:
  - T1: Upload locations → Backend accepts → DB saves → Frontend receives list
  - T2: Optimize with **Qwen** → Returns optimized route → Frontend displays
  - T3: Fallback mechanism: **Qwen fails → T-Pro is used → Result is returned**
  - T4: Fallback chain: **T-Pro fails → Llama is used**
  - T5: All models fail: **All LLM models unavailable → error returned**
  - T6: Compare models → **All 3 models (Qwen, T-Pro, Llama) run → Results returned**
  - T7: Error scenario: Invalid locations → Backend rejects → Frontend shows error
  - T8: Performance: Optimize 50 locations → Response < 5 sec
  - **T9 (NEW)**: Model selection: Verify correct model chosen based on constraints
  - **T10 (NEW)**: Fallback tracking: Verify fallback_reason field recorded in DB
- ✅ Используй pytest для backend, Jest/Vitest для frontend
- ✅ CI/CD integration (GitHub Actions runs tests)
- ✅ Coverage report генерируется
- ✅ Test data включает реалистичные locations (50+ магазинов в Москве)

**Test examples**:
```python
def test_qwen_optimization():
    # Should use Qwen by default
    response = client.post("/api/v1/optimize", json=payload)
    assert response["model_used"] == "Qwen"

def test_qwen_fallback_to_tpro():
    # If Qwen times out, should fallback to T-Pro
    with mock.patch('qwen.timeout'):
        response = client.post("/api/v1/optimize", json=payload)
        assert response["model_used"] == "T-Pro"
        assert "timeout" in response["fallback_reason"]

def test_all_models_fail_returns_error():
    # If all LLM models fail, return error
    with mock.patch('qwen.error'), \
         mock.patch('tpro.error'), \
         mock.patch('llama.error'):
        response = client.post("/api/v1/optimize", json=payload)
        assert response.status_code == 503
        assert response["fallback_reason"] == "All LLM models unavailable"
```

---

### QA-3: MVP Demo Preparation & Stakeholder Communication

**Приоритет**: 🔴 HIGH

**Оценка**: 4 часа

**Описание**:
Подготовить все материалы для MVP демонстрации с НОВЫМИ 3 LLM моделями.

**Acceptance Criteria**: (same as before, but updated with new models)

**Key points to demo**:
- Upload locations
- Optimize with Qwen (PRIMARY)
- Show fallback mechanism (if Qwen is simulated to fail → T-Pro used)
- Show comparison of all 3 models (Qwen, T-Pro, Llama)
- Show Analytics with new models
- Explain model selection logic

---

## 📋 SUMMARY ТАБЛИЦА (UPDATED)

| ID | Название | Приоритет | Часы | Models Used |
|----|----------|-----------|------|-------------|
| BE-7 | DB schema | 🔴 HIGH | 4ч | Qwen, T-Pro, Llama |
| BE-8 | POST /locations/upload | 🔴 HIGH | 3ч | N/A |
| BE-9 | Route optimizer алгоритм | 🔴 HIGH | 8ч | **Qwen, T-Pro, Llama** ✨ |
| BE-10 | POST /optimize endpoint | 🔴 HIGH | 4ч | **Qwen, T-Pro, Llama** ✨ |
| BE-11 | GET /metrics endpoint | 🟡 MED | 3ч | **Qwen, T-Pro, Llama** ✨ |
| BE-12 | LLM insights интеграция | 🟡 MED | 5ч | **Qwen, T-Pro, Llama** ✨ |
| BE-13 | GET /compare endpoint | 🟡 MED | 4ч | **Qwen, T-Pro, Llama** ✨ |
| FE-6 | Real API integration | 🔴 HIGH | 3ч | N/A |
| FE-7 | File upload компонент | 🔴 HIGH | 5ч | N/A |
| FE-8 | Optimize форма логика | 🔴 HIGH | 6ч | N/A |
| FE-9 | Dashboard real data | 🟡 MED | 5ч | Shows all 3 models |
| FE-10 | Analytics page | 🟡 MED | 6ч | Shows all 3 models |
| ML-4 | Quality evaluation | 🔴 HIGH | 4ч | **Works with all 3 models** ✨ |
| ML-5 | Model comparison | 🟡 MED | 6ч | **Qwen, T-Pro, Llama** ✨ |
| ML-6 | Model selector | 🟡 MED | 4ч | **Qwen, T-Pro, Llama** ✨ |
| QA-2 | Integration testing | 🔴 HIGH | 8ч | **Tests all 3 models + fallback** ✨ |
| QA-3 | Demo prep | 🔴 HIGH | 4ч | **Demonstrates all 3 models** ✨ |
| | | | | |
| | **ИТОГО** | | **83 часа** | |

---

## 🔄 KEY CHANGES FROM OLD WEEK 2:

| Параметр | Было | Стало |
|----------|-----|-------|
| Models | GigaChat, Cotype, T-Pro | **Qwen, T-Pro, Llama** ✨ |
| BE-9 algorithm | Uses GigaChat primary | **Uses Qwen primary** ✨ |
| BE-10 response | model_used: "GigaChat" | **model_used: "Qwen"** ✨ |
| BE-12 insights | Uses GigaChat/Cotype | **Uses Qwen/T-Pro/Llama** ✨ |
| BE-13 comparison | Compares 3 old models | **Compares 3 new models** ✨ |
| ML-5 benchmark | Benchmarks old models | **Benchmarks new models** ✨ |
| ML-6 selector | Selects old models | **Selects new models** ✨ |
| QA-2 tests | Tests old models | **Tests new models** ✨ |
| QA-3 demo | Demos old models | **Demos new models** ✨ |

---

## 🎯 SUCCESS CRITERIA WEEK 2 (UPDATED):

**GO** if:
- ✅ Qwen optimization works
- ✅ **Fallback to T-Pro works** (if Qwen fails)
- ✅ **Fallback to Llama works** (if T-Pro fails)
- ✅ **Comparison shows all 3 models** (Qwen, T-Pro, Llama)
- ✅ Integration tests pass (including fallback chain)
- ✅ No critical bugs
- ✅ Performance: < 5 sec for 50 locations

---
