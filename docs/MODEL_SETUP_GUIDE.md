# Руководство по установке и запуску моделей

Пошаговое руководство для скачивания и локального запуска каждой из трех LLM моделей проекта.

---

## Общие требования

### Программное обеспечение
- Python 3.11+
- Git
- pip (менеджер пакетов Python)

### Установка llama-cpp-python

Все три модели используют библиотеку `llama-cpp-python` для инференса GGUF файлов.

**Без GPU (только CPU)**:
```bash
pip install llama-cpp-python
```

**С поддержкой NVIDIA GPU (CUDA)**:
```bash
# Windows / Linux
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
```

На Windows может потребоваться установка [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) и CUDA Toolkit.

**Проверка установки**:
```bash
python -c "from llama_cpp import Llama; print('OK')"
```

### Оценка ресурсов

| Модель | VRAM (GPU) | RAM (CPU) | Диск | Рекомендация |
|--------|-----------|-----------|------|--------------|
| Qwen2-0.5B (Q4_K_M) | ~0.5 GB | ~1 GB | ~0.4 GB | Ноутбук / любой ПК |
| T-Pro (Q4_K_M) | ~4-8 GB | ~8-16 GB | ~4-8 GB | Стационарный ПК |
| Llama-3.2-1B (Q4_K_M) | ~1 GB | ~2 GB | ~0.8 GB | Ноутбук / любой ПК |

> Квантованные версии (Q4_K_M, Q5_K_M) значительно уменьшают требования к памяти.
> Для ноутбука рекомендуется начать с Qwen (самая маленькая) и Llama.

---

## 1. Qwen (Primary модель)

### Описание
- **Модель**: Qwen2-0.5B-Instruct
- **Роль в проекте**: Primary (основная, лучшее качество)
- **Размер**: ~0.5B параметров, GGUF ~400 MB (Q4_K_M)
- **Hugging Face**: [Qwen/Qwen2-0.5B-Instruct-GGUF](https://huggingface.co/Qwen/Qwen2-0.5B-Instruct-GGUF)

### Шаг 1: Скачать GGUF файл

**Вариант A — через huggingface-cli**:
```bash
pip install huggingface-hub

# Скачать квантованную модель Q4_K_M
huggingface-cli download Qwen/Qwen2-0.5B-Instruct-GGUF qwen2-0_5b-instruct-q4_k_m.gguf --local-dir ./backend/src/models/
```

**Вариант B — вручную**:
1. Перейти на https://huggingface.co/Qwen/Qwen2-0.5B-Instruct-GGUF
2. Найти файл `qwen2-0_5b-instruct-q4_k_m.gguf` (или другую квантизацию)
3. Скачать и поместить в `backend/src/models/`

### Шаг 2: Настроить .env

В файле `backend/.env`:
```env
QWEN_API_ENDPOINT=local
QWEN_MODEL_ID=qwen2-0_5b-instruct-q4_k_m.gguf
```

> `QWEN_MODEL_ID` — это имя файла. Система ищет его в трех местах:
> 1. Как абсолютный/относительный путь
> 2. В `backend/src/models/`
> 3. В `backend/`

### Шаг 3: Проверить работоспособность

```bash
cd backend
python -m uvicorn src.main:app --reload
```

Отправить тестовый запрос:
```bash
curl -X POST http://127.0.0.1:8000/qwen/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "locations": [
      {"ID": "loc_1", "name": "Красная площадь", "address": "Красная площадь, Москва", "lat": 55.7539, "lon": 37.6208, "time_window_start": "10:00", "time_window_end": "22:00", "priority": "high"},
      {"ID": "loc_2", "name": "Парк Горького", "address": "Крымский Вал 9, Москва", "lat": 55.7298, "lon": 37.5995, "time_window_start": "08:00", "time_window_end": "23:00", "priority": "medium"}
    ],
    "constraints": {}
  }'
```

**Ожидаемый результат**: JSON с оптимизированным маршрутом и `model_used`.

### Параметры модели в коде
- `n_threads=4` (потоки CPU)
- `n_gpu_layers=0` (GPU отключен по умолчанию)
- `n_ctx=2048` (размер контекста)
- `timeout=120` секунд

---

## 2. T-Pro (Secondary модель)

### Описание
- **Модель**: T-Pro-it-1.0
- **Роль в проекте**: Secondary (быстрый отклик)
- **Размер**: крупная модель, GGUF ~4-8 GB (Q4_K_M)
- **Hugging Face**: [t-tech/T-pro-it-1.0](https://huggingface.co/t-tech/T-pro-it-1.0)

> T-Pro — крупная модель. Для локального запуска нужна квантованная GGUF версия.

### Шаг 1: Найти и скачать GGUF файл

Поищите квантованную GGUF версию на Hugging Face. Если официальной GGUF нет, можно:

**Вариант A — искать community GGUF версии**:
```bash
# Поиск на huggingface
huggingface-cli search t-pro gguf
```

Или проверьте: https://huggingface.co/models?search=t-pro+gguf

**Вариант B — конвертировать самостоятельно**:
```bash
# Клонировать llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Конвертировать в GGUF
python convert_hf_to_gguf.py --model t-tech/T-pro-it-1.0 --outfile t-pro-it-1.0.gguf

# Квантовать для уменьшения размера
./llama-quantize t-pro-it-1.0.gguf t-pro-it-1.0-q4_k_m.gguf Q4_K_M
```

### Шаг 2: Поместить файл и настроить .env

Скопировать GGUF файл в `backend/src/models/`, затем в `backend/.env`:
```env
TPRO_API_ENDPOINT=local
TPRO_MODEL_ID=t-pro-it-1.0-q4_k_m.gguf
```

### Шаг 3: Проверить работоспособность

```bash
cd backend
python -m uvicorn src.main:app --reload
```

Тестовый запрос:
```bash
curl -X POST http://127.0.0.1:8000/tpro/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "locations": [
      {"ID": "loc_1", "name": "Красная площадь", "address": "Красная площадь, Москва", "lat": 55.7539, "lon": 37.6208, "time_window_start": "10:00", "time_window_end": "22:00", "priority": "high"},
      {"ID": "loc_2", "name": "Парк Горького", "address": "Крымский Вал 9, Москва", "lat": 55.7298, "lon": 37.5995, "time_window_start": "08:00", "time_window_end": "23:00", "priority": "medium"}
    ],
    "constraints": {}
  }'
```

### Параметры модели в коде
- `n_threads=4` (потоки CPU)
- `n_gpu_layers=0` (GPU отключен)
- `n_ctx=512` (короткий контекст для скорости)
- `timeout=30` секунд (быстрее других)

### Предупреждение
T-Pro — самая требовательная модель. На ноутбуке без GPU может работать медленно. Рекомендации:
- Использовать квантизацию Q4_K_M или Q3_K_M
- Запускать на стационарном ПК с 16+ GB RAM
- Если GPU доступен, установить `n_gpu_layers=-1` для автоматического использования

---

## 3. Llama (Fallback модель)

### Описание
- **Модель**: Llama-3.2-1B-Instruct
- **Роль в проекте**: Fallback (максимальная надежность, open-source)
- **Размер**: ~1B параметров, GGUF ~0.8 GB (Q4_K_M)
- **Hugging Face**: [bartowski/Llama-3.2-1B-Instruct-GGUF](https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF)

> Llama — gated модель. Нужно принять лицензию на Hugging Face перед скачиванием.

### Шаг 1: Получить доступ

1. Зайти на https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct
2. Нажать "Request access" и принять лицензию Meta
3. Дождаться одобрения (обычно мгновенно)
4. Получить HF токен: https://huggingface.co/settings/tokens

### Шаг 2: Скачать GGUF файл

```bash
pip install huggingface-hub

# Логин (потребуется токен)
huggingface-cli login

# Скачать квантованную версию
huggingface-cli download bartowski/Llama-3.2-1B-Instruct-GGUF Llama-3.2-1B-Instruct-Q4_K_M.gguf --local-dir ./backend/src/models/
```

Или скачать вручную со страницы: https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF

### Шаг 3: Настроить .env

В файле `backend/.env`:
```env
LLAMA_API_ENDPOINT=local
LLAMA_MODEL_ID=Llama-3.2-1B-Instruct-Q4_K_M.gguf
HF_TOKEN=hf_ваш_токен_здесь
```

### Шаг 4: Проверить работоспособность

```bash
cd backend
python -m uvicorn src.main:app --reload
```

Тестовый запрос:
```bash
curl -X POST http://127.0.0.1:8000/llama/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "locations": [
      {"ID": "loc_1", "name": "Красная площадь", "address": "Красная площадь, Москва", "lat": 55.7539, "lon": 37.6208, "time_window_start": "10:00", "time_window_end": "22:00", "priority": "high"},
      {"ID": "loc_2", "name": "Парк Горького", "address": "Крымский Вал 9, Москва", "lat": 55.7298, "lon": 37.5995, "time_window_start": "08:00", "time_window_end": "23:00", "priority": "medium"}
    ],
    "constraints": {}
  }'
```

### Параметры модели в коде
- `n_threads=8` (больше потоков для надежности)
- `n_gpu_layers=-1` (автоматически используй GPU если есть)
- `n_ctx=4096` (большой контекст)
- `timeout=120` секунд

---

## Быстрая проверка всех моделей (ML скрипт)

Помимо backend, можно проверить модели через ML скрипт, который использует Hugging Face Transformers:

```bash
# Установить ML зависимости
pip install -r ml/requirements.txt

# Запустить проверку
python ml/test_models.py
```

Скрипт проверит доступность всех трех моделей (Qwen, T-Pro, Llama) через Hugging Face и выведет статус каждой.

Результаты: `ml/models/test_results.json`

---

## Таблица: с чего начать

### На ноутбуке (8 GB RAM, без GPU)

| Приоритет | Модель | Почему |
|-----------|--------|--------|
| 1 | **Qwen** | Маленькая (~400 MB), быстрая на CPU |
| 2 | **Llama** | Небольшая (~800 MB), надежная |
| 3 | T-Pro | Крупная, может быть медленной без GPU |

### На стационарном ПК (16+ GB RAM, с GPU)

| Приоритет | Модель | Почему |
|-----------|--------|--------|
| 1 | **Все три** | Достаточно ресурсов для всех |
| Совет | Включи `n_gpu_layers=-1` | Автоматически использует GPU |

---

## Пример .env для локального запуска всех трех моделей

```env
# === LLM Модели (локальные GGUF файлы) ===
QWEN_API_ENDPOINT=local
QWEN_MODEL_ID=qwen2-0_5b-instruct-q4_k_m.gguf

TPRO_API_ENDPOINT=local
TPRO_MODEL_ID=t-pro-it-1.0-q4_k_m.gguf

LLAMA_API_ENDPOINT=local
LLAMA_MODEL_ID=Llama-3.2-1B-Instruct-Q4_K_M.gguf

# Hugging Face токен (для Llama gated модели)
HF_TOKEN=hf_ваш_токен

# === Остальные настройки ===
DATABASE_URL=postgresql://user:password@localhost/t2_db
BACKEND_PORT=8000
FRONTEND_PORT=5173
VITE_API_URL=http://localhost:8000
ENVIRONMENT=development
DEBUG=true
```

---

## Устранение неполадок

### "GGUF model file not found"
- Проверь, что файл лежит в `backend/src/models/` или `backend/`
- Проверь, что имя файла в `.env` совпадает с реальным именем файла
- Путь к файлу чувствителен к регистру на Linux/macOS

### "Please install llama-cpp-python"
```bash
pip install llama-cpp-python
```

### Модель загружается очень долго
- Первая загрузка GGUF может занять 10-30 секунд (инициализация)
- Последующие запросы будут быстрее (модель кэшируется в памяти)
- Если на CPU — это нормально, особенно для T-Pro

### Out of Memory
- Используйте более агрессивную квантизацию (Q3_K_S вместо Q4_K_M)
- Уменьшите `n_ctx` (контекст) в клиенте
- Закройте другие приложения
- Запускайте модели по одной, а не все сразу

### Llama: "Access denied" / "Gated model"
1. Перейти на https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct
2. Принять лицензию Meta
3. Убедиться, что `HF_TOKEN` в `.env` корректный
4. Попробовать: `huggingface-cli whoami` (проверка авторизации)

### GPU не используется
```bash
# Проверить CUDA
python -c "import torch; print(torch.cuda.is_available())"

# Переустановить llama-cpp-python с CUDA
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
```

---

## Полезные ссылки

- [Qwen2-0.5B-Instruct](https://huggingface.co/Qwen/Qwen2-0.5B-Instruct) — страница модели
- [Qwen2-0.5B-Instruct-GGUF](https://huggingface.co/Qwen/Qwen2-0.5B-Instruct-GGUF) — GGUF версия
- [T-Pro-it-1.0](https://huggingface.co/t-tech/T-pro-it-1.0) — страница модели
- [Llama-3.2-1B-Instruct](https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct) — страница модели
- [bartowski/Llama-3.2-1B-Instruct-GGUF](https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF) — GGUF версия
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) — библиотека для инференса
- [llama.cpp](https://github.com/ggerganov/llama.cpp) — конвертация и квантизация моделей
