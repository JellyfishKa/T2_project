# Тест-план - Неделя 3: Переход на 2 LLM и Production-Ready

## 1. Введение

Этот документ описывает стратегию тестирования для недели 3, которая фокусируется на переходе с 3 LLM моделей (Qwen, T-Pro, Llama) на 2 модели (Qwen, Llama), стабилизации системы и подготовке к production.

## 2. Изменения архитектуры

| | Неделя 2 | Неделя 3 |
|---|---|---|
| **Primary** | Qwen | Qwen |
| **Secondary** | T-Pro | — удалена |
| **Fallback** | Llama | Llama |

## 3. Объем тестирования (Scope)

- **Компоненты**: QwenClient, LlamaClient, RouteOptimizer, Fallback chain
- **Модели**: Qwen (Primary), Llama (Fallback)
- **Целевое покрытие кода (Coverage)**: > 85%

## 4. Тест-кейсы (Test Cases)

### 4.1. Обновлённый Fallback Mechanism

*Цель*: Проверить корректность новой fallback-цепочки без T-Pro.

#### TC-FB3-001: Qwen → Llama fallback
- **Описание**: При недоступности Qwen сразу используется Llama
- **Вход**: Симуляция ошибки Qwen
- **Ожидаемый результат**: model_used="Llama", fallback_reason содержит описание ошибки
- **Примечание**: T-Pro больше не используется

#### TC-FB3-002: Qwen → Llama → error fallback chain
- **Описание**: Полная fallback-цепочка
- **Вход**: Симуляция ошибки Qwen и Llama
- **Ожидаемый результат**: Возвращается ошибка с fallback_reason="All LLM models unavailable"

#### TC-FB3-003: No T-Pro references
- **Описание**: Проверить отсутствие ссылок на T-Pro в коде
- **Ожидаемый результат**: Никакие API responses не содержат "T-Pro" или "tpro"

### 4.2. Qwen Client (Primary)

*Цель*: Проверить стабильность работы Qwen как основной модели.

#### TC-QWEN-001: Successful optimization
- **Описание**: Успешная оптимизация маршрута через Qwen
- **Вход**: 50 locations
- **Ожидаемый результат**: optimized_route, model_used="Qwen", quality_score > 80

#### TC-QWEN-002: Timeout handling
- **Описание**: Обработка таймаута Qwen
- **Вход**: Симуляция медленного ответа (>30 сек)
- **Ожидаемый результат**: Fallback на Llama

#### TC-QWEN-003: Rate limit handling
- **Описание**: Обработка rate limit (429)
- **Ожидаемый результат**: Fallback на Llama с соответствующим fallback_reason

### 4.3. Llama Client (Fallback)

*Цель*: Проверить надёжность Llama как fallback модели.

#### TC-LLAMA-001: Successful fallback
- **Описание**: Успешная оптимизация через Llama после падения Qwen
- **Ожидаемый результат**: optimized_route, model_used="Llama"

#### TC-LLAMA-002: CPU mode operation
- **Описание**: Работа Llama в CPU режиме
- **Ожидаемый результат**: Корректная оптимизация (медленнее, но работает)

#### TC-LLAMA-003: Memory constraints
- **Описание**: Работа при ограниченной памяти
- **Ожидаемый результат**: Graceful degradation или возврат ошибки

### 4.4. Production Readiness

*Цель*: Проверить готовность к production.

#### TC-PROD-001: Health check endpoint
- **Описание**: GET /health возвращает статус всех компонентов
- **Ожидаемый результат**: {"qwen": "available", "llama": "available", "database": "connected"}

#### TC-PROD-002: Error logging
- **Описание**: Все ошибки логируются с достаточным контекстом
- **Ожидаемый результат**: Логи содержат model_used, fallback_reason, timestamp

#### TC-PROD-003: Graceful degradation
- **Описание**: Система продолжает работать при частичных отказах
- **Ожидаемый результат**: Всегда возвращается валидный ответ (через fallback chain)

#### TC-PROD-004: Performance benchmarks
- **Описание**: Производительность соответствует требованиям
- **Ожидаемый результат**:
  - Qwen: ~2-3 сек для 50 locations
  - Llama: ~4-5 сек для 50 locations

### 4.6. UI Updates

*Цель*: Проверить обновления UI для 2 моделей.

#### TC-UI-001: Model selector shows 2 models
- **Описание**: Селектор моделей показывает только Qwen и Llama
- **Ожидаемый результат**: Dropdown содержит только "Qwen" и "Llama"

#### TC-UI-002: Dashboard shows 2 models
- **Описание**: Dashboard сравнивает только Qwen и Llama
- **Ожидаемый результат**: Comparison table содержит 2 строки (Qwen и Llama)

#### TC-UI-003: No T-Pro in analytics
- **Описание**: Analytics страница не показывает T-Pro
- **Ожидаемый результат**: Все графики только для Qwen и Llama

### 4.7. Regression Testing

*Цель*: Проверить, что изменения не сломали существующий функционал.

#### TC-REG-001: All Week 1 tests pass
- **Описание**: Все тесты недели 1 проходят
- **Ожидаемый результат**: pytest backend/tests/ - все passed

#### TC-REG-002: All Week 2 tests pass (updated)
- **Описание**: Все тесты недели 2 проходят с обновлениями
- **Ожидаемый результат**: Integration tests проходят без T-Pro

## 5. Инструменты и Инфраструктура

- **Фреймворк Backend**: pytest + pytest-asyncio
- **Фреймворк Frontend**: Vitest
- **Мокинг**: unittest.mock / pytest-mock
- **CI/CD**: GitHub Actions
- **Coverage**: pytest-cov

## 6. Стратегия выполнения

1. Обновить тесты для удаления T-Pro
2. Запустить: `pytest backend/tests/ -v`
3. Запустить ML тесты: `pytest ml/tests/ -v`
4. Запустить frontend тесты: `npm run test:run`
5. Проверить покрытие: `pytest --cov=backend/src backend/tests/ --cov-report=term-missing`
6. Запустить type-check: `npm run type-check`

## 7. Критерии приёмки

- [ ] T-Pro полностью удалён из тестов и кода
- [ ] Fallback цепочка Qwen → Llama → ошибка работает
- [ ] Все API endpoints работают корректно
- [ ] UI показывает только 2 модели (Qwen, Llama)
- [ ] Performance соответствует требованиям
- [ ] Coverage > 85%
- [ ] Все тесты проходят
- [ ] TypeScript type-check проходит