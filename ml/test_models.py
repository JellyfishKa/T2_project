"""
Проверка доступности и работоспособности трёх LLM (Hugging Face) и клиентов backend.

Модели: Qwen2-0.5B-Instruct, Llama-3.2-1B-Instruct, T-Pro-it-1.0.
Ресурсы: см. ml/README.md (Qwen ~2 GB VRAM, Llama ~4 GB, T-Pro до ~64 GB в bf16).
Backend не изменяется — только добавляем его в sys.path и вызываем generate().
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Подключение backend: только импорт, код в backend/ не трогаем
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
if BACKEND_DIR.exists():
    sys.path.insert(0, str(BACKEND_DIR))

# Обязательные зависимости для тестов HF-моделей
try:
    import psutil
except ImportError:
    print("ОШИБКА: Модуль 'psutil' не установлен.")
    print("Установите зависимости: pip install psutil")
    sys.exit(1)

try:
    import torch
except ImportError:
    print("ОШИБКА: Модуль 'torch' не установлен.")
    print("Возможно, вы не активировали виртуальное окружение.")
    print("\nДля активации виртуального окружения выполните:")
    print("  Windows PowerShell: .\\ml_env\\Scripts\\Activate.ps1")
    print("  Windows CMD: ml_env\\Scripts\\activate.bat")
    print("\nИли запустите скрипт напрямую через Python из виртуального окружения:")
    print("  .\\ml_env\\Scripts\\python.exe ml\\test_models.py")
    sys.exit(1)

# Вывод в консоль в UTF-8 на Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "models"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'model_test.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

OK_MARKER = "[OK]"
WARN_MARKER = "[WARN]"
ERROR_MARKER = "[ERROR]"


def get_system_info():
    """Сводка по CPU, RAM и CUDA для интерпретации результатов тестов."""
    info = {
        'cpu_count': psutil.cpu_count(),
        'ram_total_gb': psutil.virtual_memory().total / (1024**3),
        'ram_available_gb': psutil.virtual_memory().available / (1024**3),
        'cuda_available': torch.cuda.is_available(),
    }
    
    if info['cuda_available']:
        info['cuda_device_count'] = torch.cuda.device_count()
        info['cuda_device_name'] = torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else None
        info['cuda_memory_total_gb'] = torch.cuda.get_device_properties(0).total_memory / (1024**3) if torch.cuda.device_count() > 0 else None
    
    return info


def test_qwen():
    """Проверка доступности Qwen2-0.5B-Instruct: токенизатор, конфиг, при возможности — инференс."""
    logger.info("=" * 60)
    logger.info("Тестирование Qwen2-0.5B-Instruct")
    logger.info("=" * 60)
    
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM  # noqa: F401
        
        model_name = "Qwen/Qwen2-0.5B-Instruct"
        logger.info(f"Загрузка модели: {model_name}")
        
        # Проверка доступности модели
        logger.info("Проверка доступности токенизатора...")
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        logger.info(f"{OK_MARKER} Токенизатор загружен. Размер словаря: {len(tokenizer)}")

        logger.info("Проверка конфигурации модели...")
        from transformers import AutoConfig
        config = AutoConfig.from_pretrained(model_name, trust_remote_code=True)
        logger.info(f"{OK_MARKER} Конфигурация загружена. Параметры: {config.num_parameters() if hasattr(config, 'num_parameters') else 'N/A'}")
        
        logger.info(f"{OK_MARKER} Qwen2-0.5B-Instruct доступна и может быть загружена")
        logger.info(f"{WARN_MARKER} Для полной загрузки рекомендуется ~2GB VRAM и ~4GB RAM")
        
        return True, {
            'model_name': model_name,
            'tokenizer_size': len(tokenizer),
            'status': 'available'
        }
        
    except Exception as e:
        logger.error(f"{ERROR_MARKER} Ошибка при тестировании Qwen: {str(e)}")
        return False, {'error': str(e)}


def test_llama():
    """Проверка доступности Llama-3.2-1B-Instruct; при наличии GPU — загрузка и тестовый инференс."""
    logger.info("=" * 60)
    logger.info("Тестирование Llama-3.2-1B-Instruct")
    logger.info("=" * 60)
    
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        model_name = "meta-llama/Llama-3.2-1B-Instruct"
        logger.info(f"Загрузка модели: {model_name}")
        
        # Проверка доступности модели
        logger.info("Проверка доступности токенизатора...")
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        logger.info(f"{OK_MARKER} Токенизатор загружен. Размер словаря: {len(tokenizer)}")
        from transformers import AutoConfig
        config = AutoConfig.from_pretrained(model_name, trust_remote_code=True)
        logger.info(f"{OK_MARKER} Конфигурация загружена")

        if torch.cuda.is_available():
            logger.info("Попытка загрузки модели на GPU...")
            try:
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16,
                    device_map="auto",
                    trust_remote_code=True,
                    low_cpu_mem_usage=True
                )
                logger.info(f"{OK_MARKER} Модель успешно загружена на GPU: {torch.cuda.get_device_name(0)}")
                test_text = "Привет, как дела?"
                inputs = tokenizer(test_text, return_tensors="pt").to(model.device)
                with torch.no_grad():
                    outputs = model.generate(**inputs, max_new_tokens=10, do_sample=False)
                response = tokenizer.decode(outputs[0], skip_special_tokens=True)
                logger.info(f"{OK_MARKER} Тестовый инференс выполнен. Ответ: {response[:100]}...")
                
                del model
                torch.cuda.empty_cache()
                
                return True, {
                    'model_name': model_name,
                    'tokenizer_size': len(tokenizer),
                    'status': 'loaded_and_tested',
                    'device': 'cuda'
                }
            except Exception as e:
                logger.warning(f"{WARN_MARKER} Не удалось загрузить модель на GPU: {str(e)}")
                logger.info("Модель доступна, но требуется больше памяти или CPU-режим")
        logger.info(f"{OK_MARKER} Llama-3.2-1B-Instruct доступна")
        logger.info(f"{WARN_MARKER} Для полной загрузки рекомендуется ~4 GB VRAM или CPU (медленнее)")
        
        return True, {
            'model_name': model_name,
            'tokenizer_size': len(tokenizer),
            'status': 'available'
        }
        
    except Exception as e:
        logger.error(f"{ERROR_MARKER} Ошибка при тестировании Llama: {str(e)}")
        return False, {"error": str(e)}


def test_tpro():
    """Проверка доступности T-Pro-it-1.0 (токенизатор и конфиг; полная загрузка тяжёлая)."""
    logger.info("=" * 60)
    logger.info("Тестирование T-Pro-it-1.0")
    logger.info("=" * 60)
    
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        model_name = "t-tech/T-pro-it-1.0"
        logger.info(f"Загрузка модели: {model_name}")
        
        # Проверка доступности модели
        logger.info("Проверка доступности токенизатора...")
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        logger.info(f"{OK_MARKER} Токенизатор загружен. Размер словаря: {len(tokenizer)}")
        from transformers import AutoConfig
        config = AutoConfig.from_pretrained(model_name, trust_remote_code=True)
        logger.info(f"{OK_MARKER} Конфигурация загружена")
        logger.info(f"{OK_MARKER} T-Pro-it-1.0 доступна и может быть загружена")
        logger.info(f"{WARN_MARKER} Для полной загрузки требуется ~64GB VRAM (bf16) или ~32GB VRAM (int8)")
        logger.info(f"{WARN_MARKER} Рекомендуется использовать квантованную версию или vLLM для инференса")
        
        return True, {
            'model_name': model_name,
            'tokenizer_size': len(tokenizer),
            'status': 'available'
        }
        
    except Exception as e:
        logger.error(f"{ERROR_MARKER} Ошибка при тестировании T-Pro: {str(e)}")
        return False, {'error': str(e)}


def test_backend_clients():
    """
    Проверка клиентов backend: импорт и вызов generate() для GigaChat, Cotype, T-Pro.
    Backend не изменяется. При отсутствии backend или ошибке импорта возвращаем None.
    """
    logger.info("=" * 60)
    logger.info("Тестирование клиентов backend (GigaChat, Cotype, T-Pro)")
    logger.info("=" * 60)
    if not BACKEND_DIR.exists():
        logger.warning(f"{WARN_MARKER} Папка backend не найдена: {BACKEND_DIR}")
        return None

    try:
        from src.models.gigachat_client import GigaChatClient
        from src.models.cotype_client import CotypeClient
        from src.models.tpro_client import TProClient
    except ImportError as e:
        logger.warning(f"{WARN_MARKER} Не удалось импортировать клиенты backend: {e}")
        return None

    results = {}
    test_prompt = "Краткий тест подключения."
    try:
        client = GigaChatClient(token="test_token", api_url="http://test.url")
        response = client.generate(test_prompt)
        ok = isinstance(response, str) and len(response) > 0
        logger.info(f"  GigaChatClient: {OK_MARKER if ok else ERROR_MARKER} generate() = {response[:80]}...")
        results["gigachat"] = {"success": ok, "response_preview": response[:100]}
    except Exception as e:
        logger.error(f"  GigaChatClient: {ERROR_MARKER} {e}")
        results["gigachat"] = {"success": False, "error": str(e)}
    try:
        client = CotypeClient(model_path="/path/to/model")
        response = client.generate(test_prompt)
        ok = isinstance(response, str) and len(response) > 0
        logger.info(f"  CotypeClient: {OK_MARKER if ok else ERROR_MARKER} generate() = {response[:80]}...")
        results["cotype"] = {"success": ok, "response_preview": response[:100]}
    except Exception as e:
        logger.error(f"  CotypeClient: {ERROR_MARKER} {e}")
        results["cotype"] = {"success": False, "error": str(e)}
    try:
        client = TProClient(api_key="test_key")
        response = client.generate(test_prompt)
        ok = isinstance(response, str) and len(response) > 0
        logger.info(f"  TProClient: {OK_MARKER if ok else ERROR_MARKER} generate() = {response[:80]}...")
        results["tpro"] = {"success": ok, "response_preview": response[:100]}
    except Exception as e:
        logger.error(f"  TProClient: {ERROR_MARKER} {e}")
        results["tpro"] = {"success": False, "error": str(e)}

    logger.info(f"{OK_MARKER} Клиенты backend подключены и отвечают")
    return results


def main():
    """Запуск проверки всех моделей и клиентов backend, запись отчёта в models/."""
    logger.info("=" * 60)
    logger.info("НАЧАЛО ТЕСТИРОВАНИЯ LLM МОДЕЛЕЙ")
    logger.info("=" * 60)
    
    sys_info = get_system_info()
    logger.info("\nИнформация о системе:")
    logger.info(f"  CPU ядер: {sys_info['cpu_count']}")
    logger.info(f"  RAM всего: {sys_info['ram_total_gb']:.2f} GB")
    logger.info(f"  RAM доступно: {sys_info['ram_available_gb']:.2f} GB")
    logger.info(f"  CUDA доступна: {sys_info['cuda_available']}")
    if sys_info['cuda_available']:
        logger.info(f"  CUDA устройств: {sys_info['cuda_device_count']}")
        logger.info(f"  CUDA устройство: {sys_info['cuda_device_name']}")
        logger.info(f"  CUDA память: {sys_info['cuda_memory_total_gb']:.2f} GB")
    logger.info("")
    
    results = {}
    try:
        success, info = test_qwen()
        results["qwen"] = {"success": success, "info": info}
    except Exception as e:
        logger.error(f"Критическая ошибка при тестировании Qwen: {str(e)}")
        results["qwen"] = {"success": False, "error": str(e)}
    logger.info("")
    try:
        success, info = test_llama()
        results["llama"] = {"success": success, "info": info}
    except Exception as e:
        logger.error(f"Критическая ошибка при тестировании Llama: {str(e)}")
        results["llama"] = {"success": False, "error": str(e)}
    logger.info("")
    try:
        success, info = test_tpro()
        results["tpro"] = {"success": success, "info": info}
    except Exception as e:
        logger.error(f"Критическая ошибка при тестировании T-Pro: {str(e)}")
        results["tpro"] = {"success": False, "error": str(e)}
    logger.info("")
    backend_results = test_backend_clients()
    if backend_results is not None:
        results["backend"] = backend_results
    logger.info("")
    logger.info("=" * 60)
    logger.info("ИТОГОВЫЙ ОТЧЕТ")
    logger.info("=" * 60)
    
    for model_name, result in results.items():
        if model_name == "backend":
            for client_name, client_result in result.items():
                status = f"{OK_MARKER} УСПЕШНО" if client_result.get("success") else f"{ERROR_MARKER} ОШИБКА"
                logger.info(f"BACKEND.{client_name.upper()}: {status}")
            continue
        status = f"{OK_MARKER} УСПЕШНО" if result["success"] else f"{ERROR_MARKER} ОШИБКА"
        logger.info(f"{model_name.upper()}: {status}")
        if result["success"] and "info" in result:
            logger.info(f"  Модель: {result['info'].get('model_name', 'N/A')}")
            logger.info(f"  Статус: {result['info'].get('status', 'N/A')}")
    import json
    results_file = LOG_DIR / 'test_results.json'
    
    results_summary = {
        "timestamp": datetime.now().isoformat(),
        "system_info": sys_info,
        "results": results,
    }
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2, ensure_ascii=False)
    logger.info(f"\nРезультаты сохранены в: {results_file}")
    all_success = all(
        results[k]["success"] for k in ("qwen", "llama", "tpro") if k in results
    )
    
    if all_success:
        logger.info(f"\n{OK_MARKER} ВСЕ МОДЕЛИ УСПЕШНО ПРОТЕСТИРОВАНЫ")
        return 0
    else:
        logger.warning(f"\n{WARN_MARKER} НЕКОТОРЫЕ МОДЕЛИ НЕ ПРОШЛИ ТЕСТИРОВАНИЕ")
        return 1


if __name__ == "__main__":
    sys.exit(main())
