# НЕДЕЛЯ 3: ПЕРЕХОД НА 2 LLM И PRODUCTION-READY

## Изменение архитектуры LLM

По результатам бенчмарков и опыта недель 1-2 принято решение перейти с трёх LLM-моделей (Qwen, T-Pro, Llama) на **две модели**:

| | Было (Недели 1-2) | Стало (Неделя 3+) |
|---|---|---|
| **Primary** | Qwen (основная) | Qwen (основная) |
| **Secondary** | T-Pro (вторичная) | — удалена |
| **Fallback** | Llama (резервная) | Llama (резервная) |

### Причины отказа от T-Pro

В ходе тестирования и поэтапной подготовки к продакшену выяснилось, что T-Pro работает нестабильно и отказывается корректно взаимодействовать с системой. Основные проблемы:

- T-Pro (33B параметров) показала неудовлетворительное качество работы при интеграции
- Модель отказывалась корректно обрабатывать запросы на оптимизацию
- Высокие требования к ресурсам (16-20 GB RAM) не оправдывались качеством результата
- Qwen (0.5B) и Llama (1B) обеспечивают достаточное покрытие задач при минимальных ресурсах (~1.8 GB RAM суммарно)

### Обновлённая fallback-цепочка

```
Запрос на оптимизацию
    |
    v
[Qwen] -- успех --> Ответ (model_used="qwen")
    |
  ошибка
    |
    v
[Llama] -- успех --> Ответ (model_used="llama")
    |
  ошибка
    |
    v
Возвращаем ошибку
```

---

## Актуальные endpoints

| Метод | Endpoint | Модель | Назначение |
|-------|----------|--------|------------|
| POST | /api/v1/qwen/optimize | Qwen | Оптимизация маршрута (основная) |
| POST | /api/v1/llama/optimize | Llama | Оптимизация маршрута (надежная) |
| GET | /health | — | Проверка состояния системы |

---

## Production-Ready Status

### Выполненные задачи

- [x] Удалены неиспользуемые файлы (gigachat_client, cotype_client, tpro_client, tpro route)
- [x] Удалён большой файл T-Pro модели (~15 GB)
- [x] Qwen и Llama работают стабильно
- [x] Fallback-цепочка (Qwen → Llama → ошибка) протестирована
- [x] UI отображает только две модели
- [x] Документация обновлена (переход с 3 на 2 модели)
- [x] Production-ready тестирование завершено
- [x] Docker конфигурация готова к продакшену

### Тестовое покрытие

| Компонент | Тестов | Coverage |
|-----------|--------|----------|
| Backend | 61 | 64% |
| Frontend | 182 | ~70% |
| ML | 15 | ~80% |

### Тест-планы

- [x] `docs/TEST_PLAN_WEEK1.md` - LLM Клиенты
- [x] `docs/TEST_PLAN_WEEK2.md` - Интеграция и API
- [x] `docs/TEST_PLAN_WEEK3.md` - Production-Ready

---

## Актуальная конфигурация .env

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

## Docker Deployment

### Запуск в продакшене

```bash
# Копируем .env.example в .env и настраиваем
cp .env.example .env

# Запускаем все сервисы
docker-compose up -d

# Проверяем здоровье системы
curl http://localhost:8000/health
```

### Требования к серверу

| Ресурс | Минимум | Рекомендуется |
|--------|---------|---------------|
| RAM | 4 GB | 8 GB |
| CPU | 2 cores | 4 cores |
| Disk | 10 GB | 20 GB |
| GPU | — | Optional (ускорение LLM) |

---

## Ресурсы моделей

| Модель | GGUF файл | RAM | Диск |
|--------|-----------|-----|------|
| Qwen2-0.5B-Instruct | qwen2-0_5b-instruct-q4_k_m.gguf | ~0.6 GB | ~400 MB |
| Llama-3.2-1B-Instruct | Llama-3.2-1B-Instruct-Q4_K_M.gguf | ~1.2 GB | ~808 MB |
| **Итого** | | **~1.8 GB** | **~1.2 GB** |

---

## Следующие шаги (Неделя 4+)

1. Мониторинг и логирование в продакшене
2. Оптимизация производительности
3. Расширение функционала аналитики
4. Интеграция с внешними системами