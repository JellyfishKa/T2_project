# Руководство по установке и запуску моделей

Подробное руководство по скачиванию, настройке и запуску LLM моделей проекта T2.
Описаны все варианты: запуск каждой модели отдельно, попарно и всех трёх одновременно.

---

## Содержание

1. [Обзор моделей](#1-обзор-моделей)
2. [Аппаратные требования и сценарии запуска](#2-аппаратные-требования-и-сценарии-запуска)
3. [Квантизация: варианты и выбор](#3-квантизация-варианты-и-выбор)
4. [Установка зависимостей](#4-установка-зависимостей)
5. [Скачивание моделей](#5-скачивание-моделей)
6. [Настройка .env](#6-настройка-env)
7. [Сценарии запуска](#7-сценарии-запуска)
8. [Тестирование endpoints](#8-тестирование-endpoints)
9. [Устранение неполадок](#9-устранение-неполадок)
10. [Полезные ссылки](#10-полезные-ссылки)

---

## 1. Обзор моделей

В проекте используются три LLM модели с разными ролями:

| | Qwen | T-Pro | Llama |
|---|---|---|---|
| **Полное название** | Qwen2-0.5B-Instruct | T-Pro-it-1.0 | Llama-3.2-1B-Instruct |
| **Разработчик** | Alibaba (Qwen) | T-Tech (Россия) | Meta |
| **Архитектура** | Qwen2 | Qwen2 | Llama 3.2 |
| **Параметры** | 0.5B | 33B | 1B |
| **Роль в проекте** | Primary (основная) | Secondary (вторичная) | Fallback (резервная) |
| **Сильная сторона** | Лёгкая, быстрая | Качество, русский язык | Надёжность, open-source |
| **Формат** | GGUF (через llama-cpp) | GGUF (через llama-cpp) | GGUF (через llama-cpp) |

### Стратегия fallback

```
Запрос на оптимизацию
    |
    v
[Qwen] -- успех --> Ответ (model_used="qwen")
    |
  ошибка
    |
    v
[T-Pro] -- успех --> Ответ (model_used="tpro")
    |
  ошибка
    |
    v
[Llama] -- успех --> Ответ (model_used="llama")
    |
  ошибка
    |
    v
[Greedy Algorithm] --> Ответ (model_used="greedy")
```

---

## 2. Аппаратные требования и сценарии запуска

### Потребление RAM каждой моделью (в памяти, при инференсе)

| Модель | Q2_K | Q3_K_M | Q4_K_M | Q5_K_M | Q6_K | Q8_0 |
|--------|------|--------|--------|--------|------|------|
| **Qwen (0.5B)** | ~0.4 GB | ~0.5 GB | ~0.6 GB | ~0.7 GB | ~0.8 GB | ~1.0 GB |
| **T-Pro (33B)** | ~14 GB | ~16 GB | ~20 GB | ~23 GB | ~27 GB | ~35 GB |
| **Llama (1B)** | ~0.8 GB | ~1.0 GB | ~1.2 GB | ~1.4 GB | ~1.6 GB | ~2.0 GB |

> Указан приблизительный объём RAM при загрузке модели в память. Операционная система и другие процессы занимают ещё 3-6 GB.

### Сколько моделей можно запустить одновременно?

Модели загружаются в RAM при первом запросе к endpoint (Lazy Loading). Пока endpoint не вызван — модель не загружена и RAM не занята.

**Важно**: сервер FastAPI запускает все три роутера, но модели грузятся в память ТОЛЬКО при первом обращении к соответствующему endpoint.

| Сценарий | Минимум RAM | Использование диска | Рекомендация |
|----------|-------------|---------------------|--------------|
| **Только Qwen** | 8 GB | ~0.4 GB | Любой ПК / ноутбук |
| **Только Llama** | 8 GB | ~0.8 GB | Любой ПК / ноутбук |
| **Только T-Pro (Q4_K_M)** | 24 GB | ~19.8 GB | Стационарный ПК |
| **Только T-Pro (Q3_K_M)** | 20 GB | ~14 GB | Стационарный ПК |
| **Только T-Pro (Q2_K)** | 16 GB | ~12 GB | ПК с 16 GB |
| **Qwen + Llama** | 8 GB | ~1.2 GB | Любой ПК / ноутбук |
| **Qwen + T-Pro (Q4_K_M)** | 24 GB | ~20.2 GB | ПК с 32 GB |
| **Llama + T-Pro (Q4_K_M)** | 24 GB | ~20.6 GB | ПК с 32 GB |
| **Все три (Q4_K_M)** | 24 GB | ~21 GB | ПК с 32 GB |
| **Все три (T-Pro Q2_K)** | 18 GB | ~13.2 GB | ПК с 24 GB |

> При 32 GB RAM можно запустить все три модели одновременно с T-Pro Q4_K_M. Останется ~8-10 GB для ОС и других процессов.

### Рекомендации по железу

**Ноутбук (8-16 GB RAM, без GPU)**:
- Запускай **Qwen + Llama** — обе лёгкие, быстрые
- T-Pro пропускай или используй Q2_K если 16 GB RAM
- Ожидаемое время ответа: 5-30 секунд на CPU

**Стационарный ПК (32 GB RAM, без GPU)**:
- Можно запустить **все три модели** одновременно
- T-Pro рекомендуется Q4_K_M (лучшее качество)
- Ожидаемое время ответа: 10-120 секунд для T-Pro на CPU

**Стационарный ПК (32 GB RAM, NVIDIA GPU 8+ GB VRAM)**:
- Все три модели одновременно
- T-Pro: часть слоёв на GPU (`n_gpu_layers` > 0) ускоряет в 3-10x
- Qwen и Llama: полностью на GPU (`n_gpu_layers=-1`)
- Ожидаемое время ответа: 2-15 секунд

---

## 3. Квантизация: варианты и выбор

### Что такое квантизация?

Квантизация — это сжатие весов модели из формата float16/float32 в более компактные форматы (4-bit, 3-bit и т.д.). Это уменьшает размер файла и потребление RAM за счёт небольшой потери качества.

### Типы квантизации GGUF

| Тип | Бит | Качество | Размер | Скорость | Когда использовать |
|-----|-----|----------|--------|----------|-------------------|
| **Q2_K** | 2-bit | Низкое | Минимальный | Быстрая | Мало RAM, нужен минимальный размер |
| **Q3_K_S** | 3-bit | Ниже среднего | Маленький | Быстрая | Компромисс размер/качество |
| **Q3_K_M** | 3-bit | Среднее | Небольшой | Быстрая | Ограниченная RAM (16 GB для T-Pro) |
| **Q4_K_S** | 4-bit | Хорошее | Средний | Средняя | Хороший баланс |
| **Q4_K_M** | 4-bit | Хорошее+ | Средний | Средняя | **Рекомендуется** для большинства случаев |
| **Q5_K_S** | 5-bit | Высокое | Большой | Медленнее | Нужно лучшее качество |
| **Q5_K_M** | 5-bit | Высокое+ | Большой | Медленнее | Максимальное качество при квантизации |
| **Q6_K** | 6-bit | Очень высокое | Крупный | Медленная | Почти lossless, много RAM |
| **Q8_0** | 8-bit | Максимальное | Крупный | Самая медленная | Нет потерь качества, очень много RAM |

> **Общее правило**: Q4_K_M — лучший баланс качества и размера. Используй его по умолчанию.

### Варианты квантизации для каждой модели

#### Qwen2-0.5B-Instruct

Репозиторий: [Qwen/Qwen2-0.5B-Instruct-GGUF](https://huggingface.co/Qwen/Qwen2-0.5B-Instruct-GGUF)

| Файл | Квантизация | Размер | RAM |
|------|-------------|--------|-----|
| `qwen2-0_5b-instruct-q2_k.gguf` | Q2_K | ~0.2 GB | ~0.4 GB |
| `qwen2-0_5b-instruct-q4_k_m.gguf` | **Q4_K_M** | ~0.4 GB | ~0.6 GB |
| `qwen2-0_5b-instruct-q8_0.gguf` | Q8_0 | ~0.6 GB | ~1.0 GB |

> Qwen настолько маленькая, что разница между квантизациями незначительна. Берите Q4_K_M.

#### T-Pro-it-1.0

| Репозиторий | Квантизация | Размер файла | RAM при загрузке |
|-------------|-------------|--------------|------------------|
| [t-tech/T-pro-it-1.0-Q4_K_M-GGUF](https://huggingface.co/t-tech/T-pro-it-1.0-Q4_K_M-GGUF) | **Q4_K_M** | ~19.8 GB | ~20 GB |
| [t-tech/T-pro-it-1.0-Q6_K-GGUF](https://huggingface.co/t-tech/T-pro-it-1.0-Q6_K-GGUF) | Q6_K | ~26.9 GB | ~27 GB |
| [t-tech/T-pro-it-1.0-Q8_0-GGUF](https://huggingface.co/t-tech/T-pro-it-1.0-Q8_0-GGUF) | Q8_0 | ~35 GB | ~35 GB |
| [al-x/T-pro-it-1.0-Q3_K_M-GGUF](https://huggingface.co/al-x/T-pro-it-1.0-Q3_K_M-GGUF) | Q3_K_M | ~14 GB | ~16 GB |
| [VOIDER/T-pro-it-1.0-Q2_K-GGUF](https://huggingface.co/VOIDER/T-pro-it-1.0-Q2_K-GGUF) | Q2_K | ~12 GB | ~14 GB |

> T-Pro — самая тяжёлая. При 32 GB RAM берите Q4_K_M. При 16 GB — Q3_K_M или Q2_K.

#### Llama-3.2-1B-Instruct

Репозиторий: [bartowski/Llama-3.2-1B-Instruct-GGUF](https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF)

| Файл | Квантизация | Размер | RAM |
|------|-------------|--------|-----|
| `Llama-3.2-1B-Instruct-Q4_K_M.gguf` | **Q4_K_M** | ~0.8 GB | ~1.2 GB |
| `Llama-3.2-1B-Instruct-Q8_0.gguf` | Q8_0 | ~1.3 GB | ~2.0 GB |

> Llama тоже маленькая. Q4_K_M — оптимальный выбор. Community репозиторий bartowski — не gated, скачивается без логина.

### Самостоятельная квантизация

Если нужна квантизация, которой нет в готовом виде:

```bash
# 1. Клонировать llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp && make

# 2. Конвертировать HF модель в GGUF (FP16)
python convert_hf_to_gguf.py --model t-tech/T-pro-it-1.0 --outfile t-pro-fp16.gguf

# 3. Квантовать до нужного уровня
./llama-quantize t-pro-fp16.gguf t-pro-q4_k_m.gguf Q4_K_M
```

> Конвертация T-Pro из HF в GGUF потребует ~70 GB свободного диска и ~64 GB RAM.

---

## 4. Установка зависимостей

### Обязательное ПО

- Python 3.11+
- pip
- Git

### Установка llama-cpp-python

Все три модели используют единую библиотеку `llama-cpp-python`.

**Без GPU (только CPU)** — подходит для большинства случаев:
```bash
pip install llama-cpp-python
```

**С поддержкой NVIDIA GPU (CUDA)**:

Предварительно нужно:
1. NVIDIA драйвер (актуальной версии)
2. [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads) (установить, перезагрузить)
3. [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) (только Windows)

Затем:
```powershell
# Windows (PowerShell)
$env:CMAKE_ARGS="-DGGML_CUDA=on"; pip install llama-cpp-python --force-reinstall --no-cache-dir
```

```bash
# Linux / macOS
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
```

**Проверка**:
```bash
python -c "from llama_cpp import Llama; print('llama-cpp-python OK')"
```

### Установка huggingface-hub (для скачивания моделей)

```bash
pip install huggingface-hub
```

---

## 5. Скачивание моделей

Все команды выполняются из **корня проекта** (`T2_project/`).

### Qwen (~400 MB, скачивается за минуту)

```powershell
python -c "from huggingface_hub import hf_hub_download; hf_hub_download('Qwen/Qwen2-0.5B-Instruct-GGUF', 'qwen2-0_5b-instruct-q4_k_m.gguf', local_dir='./backend/src/models/')"
```

### T-Pro (~19.8 GB, скачивается 10-60 минут)

```powershell
python -c "from huggingface_hub import hf_hub_download; hf_hub_download('t-tech/T-pro-it-1.0-Q4_K_M-GGUF', 't-pro-it-1.0-q4_k_m.gguf', local_dir='./backend/src/models/')"
```

Или облегчённая версия Q3_K_M (~14 GB) для экономии RAM:
```powershell
python -c "from huggingface_hub import hf_hub_download; hf_hub_download('al-x/T-pro-it-1.0-Q3_K_M-GGUF', 'T-pro-it-1.0-Q3_K_M.gguf', local_dir='./backend/src/models/')"
```

### Llama (~808 MB, скачивается за минуту)

```powershell
python -c "from huggingface_hub import hf_hub_download; hf_hub_download('bartowski/Llama-3.2-1B-Instruct-GGUF', 'Llama-3.2-1B-Instruct-Q4_K_M.gguf', local_dir='./backend/src/models/')"
```

### Проверка скачанных файлов

После скачивания в `backend/src/models/` должны быть:
```
backend/src/models/
  qwen2-0_5b-instruct-q4_k_m.gguf      (~400 MB)
  t-pro-it-1.0-q4_k_m.gguf             (~19.8 GB)
  Llama-3.2-1B-Instruct-Q4_K_M.gguf    (~808 MB)
```

---

## 6. Настройка .env

Файл `backend/.env` управляет тем, какие модели доступны серверу.

### Все три модели (рекомендуется для 32 GB RAM)

```env
QWEN_API_ENDPOINT=local
QWEN_MODEL_ID=qwen2-0_5b-instruct-q4_k_m.gguf

TPRO_API_ENDPOINT=local
TPRO_MODEL_ID=t-pro-it-1.0-q4_k_m.gguf

LLAMA_API_ENDPOINT=local
LLAMA_MODEL_ID=Llama-3.2-1B-Instruct-Q4_K_M.gguf
```

### Только Qwen + Llama (для ноутбука, 8-16 GB RAM)

```env
QWEN_API_ENDPOINT=local
QWEN_MODEL_ID=qwen2-0_5b-instruct-q4_k_m.gguf

TPRO_API_ENDPOINT=local
TPRO_MODEL_ID=placeholder.gguf

LLAMA_API_ENDPOINT=local
LLAMA_MODEL_ID=Llama-3.2-1B-Instruct-Q4_K_M.gguf
```

> `TPRO_MODEL_ID=placeholder.gguf` — сервер запустится, но endpoint `/tpro/optimize` вернёт ошибку "model not found". Qwen и Llama будут работать нормально.

### Только одна модель (минимальная конфигурация)

```env
QWEN_API_ENDPOINT=local
QWEN_MODEL_ID=qwen2-0_5b-instruct-q4_k_m.gguf

TPRO_API_ENDPOINT=local
TPRO_MODEL_ID=placeholder.gguf

LLAMA_API_ENDPOINT=local
LLAMA_MODEL_ID=placeholder.gguf
```

> Все три переменные обязательны (требование pydantic Settings). Для отсутствующих моделей укажи `placeholder.gguf`.

### Как система ищет GGUF файл

`MODEL_ID` — это имя файла. `config.py` ищет его в трёх местах по порядку:
1. Как абсолютный/относительный путь от текущей директории
2. В `backend/src/models/`
3. В `backend/`

---

## 7. Сценарии запуска

### Общий принцип

Сервер FastAPI всегда регистрирует три роутера: `/qwen`, `/tpro`, `/llama`. Но модели загружаются в RAM **только при первом запросе** к соответствующему endpoint (Lazy Loading).

Это значит:
- Сервер запустится даже если какой-то GGUF файл не найден
- Ошибка "model not found" появится только при обращении к endpoint отсутствующей модели
- RAM занимается только загруженными моделями

### Запуск сервера

Из папки `backend/`:
```powershell
cd C:\Users\Sergej\Documents\GitHub\T2_project\backend
python -m uvicorn main:app --reload
```

Сервер стартует на `http://127.0.0.1:8000`.

Swagger UI (интерактивная документация): `http://127.0.0.1:8000/docs`

### Сценарий A: Только Qwen (минимальные ресурсы)

**Что нужно**: скачан `qwen2-0_5b-instruct-q4_k_m.gguf`, RAM 8+ GB

**Использование**:
- Отправляй запросы только на `POST /qwen/optimize`
- T-Pro и Llama endpoints будут возвращать ошибку — это нормально
- Потребление RAM: ~0.6 GB (только модель) + ~0.3 GB (FastAPI/Python)

**Применение**: начальная разработка, тестирование API, ноутбук в дороге

### Сценарий B: Qwen + Llama (лёгкая связка)

**Что нужно**: скачаны оба GGUF файла, RAM 8+ GB

**Использование**:
- `POST /qwen/optimize` — основная работа
- `POST /llama/optimize` — если Qwen не справилась
- Суммарное потребление RAM (если обе загружены): ~1.8 GB
- T-Pro endpoint вернёт ошибку — нормально

**Применение**: разработка на ноутбуке, демо, большинство задач

### Сценарий C: Qwen + T-Pro (качество + русский язык)

**Что нужно**: оба GGUF файла, RAM 24+ GB (для T-Pro Q4_K_M)

**Использование**:
- `POST /qwen/optimize` — быстрые запросы
- `POST /tpro/optimize` — когда важно качество на русском
- Суммарное потребление RAM: ~20.6 GB (Qwen + T-Pro одновременно)

**Внимание**: после загрузки T-Pro в память останется мало свободной RAM. При 32 GB это нормально. При 24 GB — возможны подтормаживания ОС.

**Применение**: стационарный ПК, бенчмарк двух моделей

### Сценарий D: Все три модели (полный набор)

**Что нужно**: все три GGUF файла, RAM 32 GB

**Использование**:
- Все три endpoint работают
- Fallback chain полностью функционален
- Суммарное потребление RAM (все три загружены): ~21.8 GB
- Свободно для ОС: ~10 GB — достаточно

**Порядок загрузки в RAM**: модели грузятся при первом запросе. Рекомендуется "прогреть" их по очереди:
1. Отправить запрос на `/qwen/optimize` (загрузится Qwen, ~5 сек)
2. Отправить запрос на `/llama/optimize` (загрузится Llama, ~5 сек)
3. Отправить запрос на `/tpro/optimize` (загрузится T-Pro, ~30-60 сек)

После прогрева все последующие запросы будут быстрее.

**Применение**: production-like окружение, полный бенчмарк, демо заказчику

### Сценарий E: T-Pro с облегчённой квантизацией (16-24 GB RAM)

Если 32 GB нет, можно использовать менее тяжёлую квантизацию T-Pro:

| Квантизация T-Pro | RAM T-Pro | RAM всех трёх | Минимум общей RAM |
|-------------------|-----------|---------------|-------------------|
| Q4_K_M | ~20 GB | ~21.8 GB | 32 GB |
| Q3_K_M | ~16 GB | ~17.8 GB | 24 GB |
| Q2_K | ~14 GB | ~15.8 GB | 20 GB |

Для Q3_K_M измени `.env`:
```env
TPRO_MODEL_ID=T-pro-it-1.0-Q3_K_M.gguf
```

> Q2_K заметно теряет в качестве. Q3_K_M — хороший компромисс.

---

## 8. Тестирование endpoints

### Через Swagger UI (рекомендуется)

Открой в браузере: `http://127.0.0.1:8000/docs`

Там можно интерактивно отправлять запросы к каждому endpoint.

### Через curl (PowerShell)

**Тестовый запрос к Qwen**:
```powershell
curl -X POST http://127.0.0.1:8000/qwen/optimize -H "Content-Type: application/json" -d '{\"locations\": [{\"ID\": \"loc_1\", \"name\": \"Красная площадь\", \"address\": \"Москва\", \"lat\": 55.7539, \"lon\": 37.6208, \"time_window_start\": \"10:00\", \"time_window_end\": \"22:00\", \"priority\": \"high\"}, {\"ID\": \"loc_2\", \"name\": \"Парк Горького\", \"address\": \"Москва\", \"lat\": 55.7298, \"lon\": 37.5995, \"time_window_start\": \"08:00\", \"time_window_end\": \"23:00\", \"priority\": \"medium\"}], \"constraints\": {}}'
```

**Тестовый запрос к T-Pro** (заменить `qwen` на `tpro`):
```powershell
curl -X POST http://127.0.0.1:8000/tpro/optimize -H "Content-Type: application/json" -d '{\"locations\": [{\"ID\": \"loc_1\", \"name\": \"Красная площадь\", \"address\": \"Москва\", \"lat\": 55.7539, \"lon\": 37.6208, \"time_window_start\": \"10:00\", \"time_window_end\": \"22:00\", \"priority\": \"high\"}, {\"ID\": \"loc_2\", \"name\": \"Парк Горького\", \"address\": \"Москва\", \"lat\": 55.7298, \"lon\": 37.5995, \"time_window_start\": \"08:00\", \"time_window_end\": \"23:00\", \"priority\": \"medium\"}], \"constraints\": {}}'
```

**Тестовый запрос к Llama** (заменить `qwen` на `llama`):
```powershell
curl -X POST http://127.0.0.1:8000/llama/optimize -H "Content-Type: application/json" -d '{\"locations\": [{\"ID\": \"loc_1\", \"name\": \"Красная площадь\", \"address\": \"Москва\", \"lat\": 55.7539, \"lon\": 37.6208, \"time_window_start\": \"10:00\", \"time_window_end\": \"22:00\", \"priority\": \"high\"}, {\"ID\": \"loc_2\", \"name\": \"Парк Горького\", \"address\": \"Москва\", \"lat\": 55.7298, \"lon\": 37.5995, \"time_window_start\": \"08:00\", \"time_window_end\": \"23:00\", \"priority\": \"medium\"}], \"constraints\": {}}'
```

### Ожидаемые времена ответа (первый запрос / последующие, CPU)

| Модель | Первый запрос (с загрузкой) | Последующие запросы |
|--------|----------------------------|---------------------|
| Qwen | 5-15 сек | 3-10 сек |
| T-Pro (Q4_K_M) | 30-120 сек | 30-120 сек |
| Llama | 5-15 сек | 5-15 сек |

> T-Pro значительно медленнее на CPU из-за 33B параметров. С GPU будет в 3-10x быстрее.

---

## 9. Устранение неполадок

### "GGUF model file not found"

**Причина**: файл не найден по указанному в `.env` пути.

**Решение**:
1. Проверить, что файл лежит в `backend/src/models/`:
   ```powershell
   dir backend\src\models\*.gguf
   ```
2. Проверить, что имя файла в `.env` **точно совпадает** (регистр важен на Linux)
3. Убедиться, что в `.env` нет лишних пробелов

### "Please install llama-cpp-python"

```bash
pip install llama-cpp-python
```

Если ошибка при компиляции — убедись, что установлены:
- Windows: [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) (компонент "Desktop development with C++")
- Linux: `sudo apt install build-essential cmake`
- macOS: `xcode-select --install`

### ValidationError: Field required (tpro_model_id, llama_model_id)

**Причина**: в `.env` отсутствуют обязательные переменные.

**Решение**: все 6 переменных обязательны. Для моделей без GGUF файла укажи placeholder:
```env
TPRO_MODEL_ID=placeholder.gguf
LLAMA_MODEL_ID=placeholder.gguf
```

### Модель загружается очень долго (> 60 сек)

- **T-Pro**: это нормально для 33B модели на CPU при первой загрузке
- **Qwen/Llama**: не должно быть > 15 сек. Проверь, не занята ли RAM
- Последующие запросы быстрее — модель остаётся в памяти

### Out of Memory / Система зависает

1. Закрой другие приложения (особенно браузер с множеством вкладок)
2. Используй более агрессивную квантизацию T-Pro (Q3_K_M или Q2_K)
3. Не загружай все три модели одновременно — используй только нужные endpoints
4. Уменьши `n_ctx` в клиенте (меньше контекст = меньше RAM)

### GPU не используется

Проверить наличие CUDA:
```bash
python -c "import torch; print('CUDA:', torch.cuda.is_available())"
```

Если CUDA доступна, но llama-cpp не использует GPU — переустановить:
```powershell
# Windows (PowerShell)
$env:CMAKE_ARGS="-DGGML_CUDA=on"; pip install llama-cpp-python --force-reinstall --no-cache-dir
```
```bash
# Linux / macOS
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
```

Для этого нужен [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads).

### Ошибка при curl в PowerShell

PowerShell может конфликтовать с curl. Используй полный путь:
```powershell
curl.exe -X POST http://127.0.0.1:8000/qwen/optimize ...
```

Или используй Swagger UI: `http://127.0.0.1:8000/docs`

---

## 10. Полезные ссылки

### Модели
- [Qwen2-0.5B-Instruct](https://huggingface.co/Qwen/Qwen2-0.5B-Instruct) — страница модели
- [Qwen2-0.5B-Instruct-GGUF](https://huggingface.co/Qwen/Qwen2-0.5B-Instruct-GGUF) — GGUF версия
- [T-Pro-it-1.0](https://huggingface.co/t-tech/T-pro-it-1.0) — страница модели
- [T-Pro-it-1.0-Q4_K_M-GGUF](https://huggingface.co/t-tech/T-pro-it-1.0-Q4_K_M-GGUF) — GGUF Q4_K_M
- [Llama-3.2-1B-Instruct](https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct) — страница модели
- [bartowski/Llama-3.2-1B-Instruct-GGUF](https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF) — GGUF версия

### Инструменты
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) — Python биндинги для llama.cpp
- [llama.cpp](https://github.com/ggerganov/llama.cpp) — конвертация, квантизация, инференс GGUF
- [Hugging Face Hub](https://huggingface.co/docs/huggingface_hub) — скачивание моделей

### Параметры моделей в коде проекта

| Параметр | Qwen | T-Pro | Llama | Описание |
|----------|------|-------|-------|----------|
| `n_threads` | 4 | 4 | 8 | Потоки CPU для инференса |
| `n_gpu_layers` | 0 | 0 | -1 (auto) | Сколько слоёв на GPU |
| `n_ctx` | 2048 | 512 | 4096 | Размер контекстного окна (токены) |
| `n_batch` | 512 | 512 | 256 | Размер батча |
| `timeout` | 120 сек | 30 сек | 120 сек | Максимальное время ответа |

Файлы клиентов:
- `backend/src/models/qwen_client.py`
- `backend/src/models/tpro_client.py`
- `backend/src/models/llama_client.py`
