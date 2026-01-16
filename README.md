# T2 Project

Проект для работы с LLM моделями: GigaChat, Cotype, T-Pro.

## Структура проекта

```
T2_project/
├── docs/              # Документация проекта
├── ml/                # ML окружение и модели
│   ├── benchmarks/    # Бенчмарки производительности
│   ├── models/        # Кэш моделей и результаты
│   ├── notebooks/     # Jupyter notebooks
│   ├── test_models.py # Тестирование моделей
│   └── requirements.txt
└── README.md
```

## Быстрый старт

### 1. Настройка окружения

```bash
# Создание виртуального окружения
python3 -m venv ml_env
source ml_env/bin/activate  # Linux/Mac
# или
ml_env\Scripts\activate      # Windows

# Установка зависимостей
pip install --upgrade pip
pip install -r ml/requirements.txt
```

### 2. Тестирование моделей

```bash
python ml/test_models.py
```

### 3. Запуск бенчмарка

```bash
python ml/benchmarks/llm_benchmark.py --iterations 5
```

## Документация

- [ML Environment](ml/README.md) - Работа с LLM моделями
- [Бенчмарки](ml/benchmarks/README.md) - Тестирование производительности
- [Архитектура](docs/ARCHITECTURE.md) - Архитектура проекта

## Требования

- Python 3.9-3.12 (рекомендуется 3.12)
- PyTorch с поддержкой CUDA (для GPU)
- Минимум 16GB RAM
- Для больших моделей требуется GPU с достаточным VRAM

## Модели

- **GigaChat3-10B-A1.8B**: ~20GB VRAM
- **Cotype-Nano**: ~3GB VRAM (может работать на CPU)
- **T-Pro-it-1.0**: ~64GB VRAM

Подробнее в [ml/README.md](ml/README.md)
