# Тест-план - Неделя 2: Интеграция и API

## 1. Введение

Этот документ описывает стратегию тестирования для недели 2, которая фокусируется на интеграции Backend + Frontend + LLM моделей (Qwen, T-Pro, Llama), API endpoints и fallback механизма.

## 2. Объем тестирования (Scope)

- **Компоненты**: API endpoints, RouteOptimizer, Model Selector, Frontend-Backend интеграция
- **Модели**: Qwen (Primary), T-Pro (Secondary), Llama (Fallback)
- **Целевое покрытие кода (Coverage)**: > 80%

## 3. Тест-кейсы (Test Cases)

### 3.1. API Endpoints

*Цель*: Проверить корректность работы API endpoints.

#### TC-API-001: POST /api/v1/locations/upload
- **Описание**: Загрузка списка магазинов в БД
- **Вход**: JSON array с locations
- **Ожидаемый результат**: 201 Created, список созданных locations с ID
- **Негативный сценарий**: 400 Bad Request при невалидных данных

#### TC-API-002: POST /api/v1/optimize (Qwen)
- **Описание**: Оптимизация маршрута с использованием Qwen
- **Вход**: locations, constraints
- **Ожидаемый результат**: optimized_route, model_used="Qwen", response_time_ms
- **Негативный сценарий**: Fallback на T-Pro при недоступности Qwen

#### TC-API-003: GET /api/v1/routes/{id}/metrics
- **Описание**: Получение метрик маршрута
- **Вход**: route_id
- **Ожидаемый результат**: total_distance, total_time, total_cost, model_used
- **Негативный сценарий**: 404 Not Found при несуществующем route_id

#### TC-API-004: GET /api/v1/benchmark/compare
- **Описание**: Сравнение результатов всех 3 моделей
- **Вход**: route_id
- **Ожидаемый результат**: comparisons array с данными по Qwen, T-Pro, Llama

### 3.2. Fallback Mechanism

*Цель*: Проверить корректность fallback-цепочки.

#### TC-FB-001: Qwen → T-Pro fallback
- **Описание**: При недоступности Qwen используется T-Pro
- **Вход**: Симуляция ошибки Qwen
- **Ожидаемый результат**: model_used="T-Pro", fallback_reason содержит описание ошибки

#### TC-FB-002: T-Pro → Llama fallback
- **Описание**: При недоступности T-Pro используется Llama
- **Вход**: Симуляция ошибки Qwen и T-Pro
- **Ожидаемый результат**: model_used="Llama", fallback_reason содержит описание ошибки

#### TC-FB-003: All LLM → error
- **Описание**: При недоступности всех LLM возвращается ошибка
- **Вход**: Симуляция ошибки всех LLM
- **Ожидаемый результат**: Возвращается ошибка с fallback_reason="All LLM models unavailable"

### 3.3. Model Selection

*Цель*: Проверить логику выбора модели.

#### TC-MS-001: Small dataset → Qwen
- **Описание**: Для <50 магазинов выбирается Qwen для лучшего качества
- **Ожидаемый результат**: recommended_model="Qwen"

#### TC-MS-002: Urgent request → T-Pro
- **Описание**: Для срочных запросов выбирается T-Pro (fastest)
- **Ожидаемый результат**: recommended_model="T-Pro"

#### TC-MS-003: Large dataset → Llama
- **Описание**: Для >200 магазинов рекомендуется Llama для надёжности
- **Ожидаемый результат**: recommended_model="Llama"

### 3.4. Frontend-Backend Integration

*Цель*: Проверить интеграцию Frontend с Backend API.

#### TC-INT-001: Upload locations flow
- **Описание**: Frontend загружает locations, Backend сохраняет, Frontend отображает
- **Ожидаемый результат**: Locations отображаются в UI

#### TC-INT-002: Optimize route flow
- **Описание**: Frontend отправляет запрос на оптимизацию, Backend возвращает результат
- **Ожидаемый результат**: Optimized route отображается на карте

#### TC-INT-003: Model comparison display
- **Описание**: Frontend запрашивает сравнение моделей и отображает результаты
- **Ожидаемый результат**: Dashboard показывает метрики всех 3 моделей

### 3.5. Performance Testing

*Цель*: Проверить производительность системы.

#### TC-PERF-001: Optimize 50 locations
- **Описание**: Оптимизация 50 магазинов
- **Ожидаемый результат**: Response time < 5 секунд

#### TC-PERF-002: Concurrent requests
- **Описание**: 10 одновременных запросов на оптимизацию
- **Ожидаемый результат**: Все запросы обработаны без ошибок

## 4. Инструменты и Инфраструктура

- **Фреймворк Backend**: pytest + pytest-asyncio
- **Фреймворк Frontend**: Vitest
- **Мокинг**: unittest.mock / pytest-mock
- **CI/CD**: GitHub Actions
- **Нагрузочное тестирование**: locust (опционально)

## 5. Стратегия выполнения

1. Запустить unit тесты: `pytest backend/tests/`
2. Запустить integration тесты: `pytest backend/tests/test_integration.py`
3. Запустить frontend тесты: `npm run test:run` (в frontend/)
4. Проверить покрытие: `pytest --cov=backend/src backend/tests/`
5. Проверить CI: GitHub Actions workflow

## 6. Критерии приёмки

- [ ] Все API endpoints работают корректно
- [ ] Fallback механизм работает для всех сценариев
- [ ] Model selector корректно выбирает модель
- [ ] Frontend-Backend интеграция работает
- [ ] Performance соответствует требованиям (<5 сек для 50 locations)
- [ ] Coverage > 80%