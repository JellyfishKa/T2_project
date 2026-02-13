# ML: окружение для LLM

Каталог содержит конфигурацию и скрипты для работы с тремя LLM (Qwen, T-Pro, Llama): загрузка/проверка доступности, бенчмарки и использование в коде. Backend не изменяется — подключаем только его клиенты (QwenClient, TProClient, LlamaClient) для тестов и бенчмарков.

---

## Структура

```
ml/
├── benchmarks/       # бенчмарки (время ответа, качество, успешность, стоимость)
├── models/           # артефакты: логи тестов, results, кэш по необходимости
├── notebooks/        # эксперименты в Jupyter
├── requirements.txt
├── test_models.py    # проверка доступности HF-моделей и клиентов backend
└── README.md
```

---

## Подключение backend

В `backend/` определены клиенты с интерфейсом `generate(prompt: str) -> str`. Мы только добавляем `backend` в `sys.path` и вызываем их:

- **test_models.py** — после тестов Qwen/Llama/T-Pro проверяет, что GigaChat, Cotype и T-Pro из backend импортируются и отвечают на тестовый промпт.
- **llm_benchmark.py** — флаг `--backend`: бенчмарк гоняется по этим же клиентам; вывод в тот же `results.json`.

Запуск бенчмарка по клиентам backend (из корня репозитория):

```bash
python ml/benchmarks/llm_benchmark.py --backend --iterations 2
```

---

## Установка

### Виртуальное окружение

```bash
# Linux / macOS
python3 -m venv ml_env
source ml_env/bin/activate

# Windows
python -m venv ml_env
ml_env\Scripts\activate
```

### Зависимости

```bash
pip install --upgrade pip
pip install -r ml/requirements.txt
```

Для GPU — отдельно ставим PyTorch с нужной CUDA (см. [pytorch.org](https://pytorch.org)), например:

```bash
# CUDA 12.x
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Hugging Face

Для gated-моделей (например, Llama) нужны токен и принятие лицензии:

```bash
pip install huggingface_hub
huggingface-cli login
```

При необходимости задайте `HF_TOKEN` в окружении или в `.env`.

---

## Ресурсы по моделям

| Модель | VRAM (ориентир) | RAM (загрузка) | Примечание |
|--------|------------------|----------------|------------|
| Qwen2-0.5B-Instruct | ~2 GB | ~4 GB | Удобна для локального инференса. |
| Llama-3.2-1B-Instruct | ~4 GB | ~6 GB | Gated: нужен HF-токен и лицензия. |
| T-Pro-it-1.0 | ~64 GB (bf16) / ~32 GB (int8) | ~8 GB | Имеет смысл квантование или vLLM. |

Ссылки: [Qwen2-0.5B-Instruct](https://huggingface.co/Qwen/Qwen2-0.5B-Instruct), [Llama-3.2-1B-Instruct](https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct), [T-Pro-it-1.0](https://huggingface.co/t-tech/T-pro-it-1.0).

---

## Использование

### Проверка моделей

Проверяет доступность трёх HF-моделей (токенизатор/конфиг, при возможности — инференс) и клиентов backend:

```bash
python ml/test_models.py
```

Результаты: `ml/models/test_results.json`, лог: `ml/models/model_test.log`.

### Бенчмарк

Рекомендуется запуск из корня репозитория:

```bash
python ml/benchmarks/llm_benchmark.py
python ml/benchmarks/llm_benchmark.py --iterations 3
python ml/benchmarks/llm_benchmark.py --mock
python ml/benchmarks/llm_benchmark.py --backend --iterations 2
```

Результаты: `ml/benchmarks/results.json`, лог: `ml/benchmarks/benchmark.log`. Подробнее — в `ml/benchmarks/README.md`.

### Использование моделей в коде

**Qwen2-0.5B-Instruct** (чат-шаблон):

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

name = "Qwen/Qwen2-0.5B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    name, torch_dtype=torch.float16, device_map="auto", trust_remote_code=True
)
messages = [{"role": "user", "content": "Привет!"}]
inputs = tokenizer.apply_chat_template(
    messages, add_generation_prompt=True, return_tensors="pt"
).to(model.device)
out = model.generate(inputs, max_new_tokens=100)
print(tokenizer.decode(out[0], skip_special_tokens=True))
```

**Llama-3.2-1B-Instruct** — тот же подход: `from_pretrained` + при необходимости `apply_chat_template` по документации модели.

**T-Pro-it-1.0** — крупная модель; те же классы, для экономии памяти — `torch_dtype=torch.bfloat16`, `low_cpu_mem_usage=True` или квантование.

---

## Кэш и окружение

- Кэш Hugging Face по умолчанию: `~/.cache/huggingface/hub/`. Путь переопределяется через `HF_HOME`.
- Таймауты загрузки: при необходимости задайте `HF_HUB_DOWNLOAD_TIMEOUT` (например, 300).
- Токен для gated-моделей: `HF_TOKEN` в окружении или в `.env` (файл в git не коммитить).

---

## Логи

- Тесты моделей: `ml/models/model_test.log`, консоль.
- Бенчмарк: `ml/benchmarks/benchmark.log`, консоль.

---

## Кратко

- Первая загрузка моделей может быть долгой; нужен запас по диску (десятки GB при полном кэше).
- Для T-Pro предпочтительны квантованная версия или vLLM.
- Модели с кастомным кодом требуют `trust_remote_code=True`.
- Backend в этом репозитории не меняем; в ml только подключаем его клиенты и используем их в тестах и бенчмарках.
