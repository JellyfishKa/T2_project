# ML Environment для работы с LLM моделями

Этот каталог содержит настройки и скрипты для работы с тремя LLM моделями:
- **GigaChat3-10B-A1.8B** (ai-sage/GigaChat3-10B-A1.8B)
- **Cotype-Nano** (MTSAIR/Cotype-Nano)
- **T-Pro-it-1.0** (t-tech/T-pro-it-1.0)

## Структура проекта

```
ml/
├── benchmarks/      # Бенчмарки и тесты производительности
├── models/          # Кэш моделей и результаты тестов
├── notebooks/       # Jupyter notebooks для экспериментов
├── requirements.txt # Зависимости Python
├── test_models.py   # Скрипт для тестирования моделей
└── README.md        # Эта документация
```

## Установка

### 1. Создание виртуального окружения

```bash
# Linux/Mac/Server
python3 -m venv ml_env
source ml_env/bin/activate

# Windows
python -m venv ml_env
ml_env\Scripts\activate
```

### 2. Установка зависимостей

```bash
pip install --upgrade pip
pip install -r ml/requirements.txt
```

**Примечание:** Для использования GPU установите PyTorch с поддержкой CUDA:
```bash
# CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 3. Настройка Hugging Face

Для загрузки моделей может потребоваться авторизация в Hugging Face:

```bash
pip install huggingface_hub
huggingface-cli login
```

## Требования к ресурсам

### GigaChat3-10B-A1.8B
- **VRAM**: ~20GB (bf16) или ~10GB (fp8)
- **RAM**: ~6GB для загрузки
- **Особенности**: MoE архитектура, оптимизирована для высокой пропускной способности
- **Ссылка**: https://huggingface.co/ai-sage/GigaChat3-10B-A1.8B

### Cotype-Nano
- **VRAM**: ~3GB
- **RAM**: ~2GB
- **Особенности**: Легковесная модель, подходит для CPU/GPU
- **Ссылка**: https://huggingface.co/MTSAIR/Cotype-Nano

### T-Pro-it-1.0
- **VRAM**: ~64GB (bf16) или ~32GB (int8)
- **RAM**: ~8GB для загрузки
- **Особенности**: Большая модель, рекомендуется квантование или vLLM
- **Ссылка**: https://huggingface.co/t-tech/T-pro-it-1.0

## Использование

### Тестирование моделей

Запустите скрипт для проверки доступности всех моделей:

```bash
python ml/test_models.py
```

Скрипт:
- Проверяет доступность каждой модели
- Загружает токенизаторы и конфигурации
- Выполняет тестовый инференс (если возможно)
- Сохраняет результаты в `ml/models/test_results.json`
- Создает лог файл `ml/models/model_test.log`

### Работа с моделями в коде

#### GigaChat3

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_name = "ai-sage/GigaChat3-10B-A1.8B"
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    trust_remote_code=True
)

messages = [{"role": "user", "content": "Привет!"}]
input_tensor = tokenizer.apply_chat_template(
    messages, 
    add_generation_prompt=True, 
    return_tensors="pt"
)
outputs = model.generate(input_tensor.to(model.device), max_new_tokens=100)
response = tokenizer.decode(outputs[0], skip_special_tokens=True)
```

#### Cotype-Nano

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_name = "MTSAIR/Cotype-Nano"
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True
)

text = "Привет, как дела?"
inputs = tokenizer(text, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=100)
response = tokenizer.decode(outputs[0], skip_special_tokens=True)
```

#### T-Pro

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_name = "t-tech/T-pro-it-1.0"
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    trust_remote_code=True,
    low_cpu_mem_usage=True
)

# Использование аналогично другим моделям
```

## Кэширование моделей

Модели автоматически кэшируются в `~/.cache/huggingface/hub/` после первой загрузки.

Для изменения пути кэша установите переменную окружения:
```bash
export HF_HOME=/path/to/cache
```

## Логирование

Все логи сохраняются в:
- `ml/models/model_test.log` - детальные логи тестирования
- Консольный вывод с информацией о статусе

## Настройка на сервере

### Установка PyTorch с CUDA (если есть GPU)

```bash
# Проверить версию CUDA
nvidia-smi

# Установить PyTorch с поддержкой CUDA
# Для CUDA 12.1:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Для CUDA 11.8:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Переменные окружения

Создайте `.env` файл (не коммитится в git):

```bash
# Hugging Face токен (если требуется)
HF_TOKEN=your_token_here

# Путь к кэшу моделей
HF_HOME=/path/to/cache
```

## Примечания

- Первая загрузка моделей может занять значительное время
- Убедитесь, что у вас достаточно места на диске (несколько десятков GB)
- Для больших моделей (T-Pro) рекомендуется использовать квантование или vLLM
- Некоторые модели требуют `trust_remote_code=True` из-за кастомных компонентов
- Модели автоматически кэшируются в `~/.cache/huggingface/hub/`