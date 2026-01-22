"""
Тестовый скрипт для проверки доступности и работы всех 3 LLM моделей:
- GigaChat3-10B-A1.8B (локально через Hugging Face)
- Cotype-Nano (локально через Hugging Face)
- T-Pro-it-1.0 (локально через Hugging Face)

Требования к ресурсам:
- GigaChat3-10B-A1.8B: ~20GB VRAM (bf16), ~10GB VRAM (fp8), ~6GB RAM для загрузки
- Cotype-Nano: ~3GB VRAM, ~2GB RAM
- T-Pro-it-1.0: ~64GB VRAM (bf16), ~32GB VRAM (int8), ~8GB RAM для загрузки
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Проверка наличия необходимых модулей
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

# Настройка кодировки для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ml/models/model_test.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Текстовые маркеры вместо эмодзи для совместимости
OK_MARKER = "[OK]"
WARN_MARKER = "[WARN]"
ERROR_MARKER = "[ERROR]"


def get_system_info():
    """Получить информацию о системе"""
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


def test_gigachat():
    """Тест загрузки GigaChat3-10B-A1.8B"""
    logger.info("=" * 60)
    logger.info("Тестирование GigaChat3-10B-A1.8B")
    logger.info("=" * 60)
    
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        model_name = "ai-sage/GigaChat3-10B-A1.8B"
        logger.info(f"Загрузка модели: {model_name}")
        
        # Проверка доступности модели
        logger.info("Проверка доступности токенизатора...")
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        logger.info(f"{OK_MARKER} Токенизатор загружен. Размер словаря: {len(tokenizer)}")
        
        # Проверка конфигурации модели без полной загрузки
        logger.info("Проверка конфигурации модели...")
        from transformers import AutoConfig
        config = AutoConfig.from_pretrained(model_name, trust_remote_code=True)
        logger.info(f"{OK_MARKER} Конфигурация загружена. Параметры: {config.num_parameters() if hasattr(config, 'num_parameters') else 'N/A'}")
        
        logger.info(f"{OK_MARKER} GigaChat3-10B-A1.8B доступна и может быть загружена")
        logger.info(f"{WARN_MARKER} Для полной загрузки требуется ~20GB VRAM (bf16) или ~10GB VRAM (fp8)")
        
        return True, {
            'model_name': model_name,
            'tokenizer_size': len(tokenizer),
            'status': 'available'
        }
        
    except Exception as e:
        logger.error(f"{ERROR_MARKER} Ошибка при тестировании GigaChat: {str(e)}")
        return False, {'error': str(e)}


def test_cotype():
    """Тест загрузки Cotype-Nano"""
    logger.info("=" * 60)
    logger.info("Тестирование Cotype-Nano")
    logger.info("=" * 60)
    
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        model_name = "MTSAIR/Cotype-Nano"
        logger.info(f"Загрузка модели: {model_name}")
        
        # Проверка доступности модели
        logger.info("Проверка доступности токенизатора...")
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        logger.info(f"{OK_MARKER} Токенизатор загружен. Размер словаря: {len(tokenizer)}")
        
        # Проверка конфигурации модели
        logger.info("Проверка конфигурации модели...")
        from transformers import AutoConfig
        config = AutoConfig.from_pretrained(model_name, trust_remote_code=True)
        logger.info(f"{OK_MARKER} Конфигурация загружена")
        
        # Попытка легкой загрузки модели (если есть GPU)
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
                
                # Тестовый инференс
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
                logger.info("Модель доступна, но требуется больше памяти или CPU режим")
        
        logger.info(f"{OK_MARKER} Cotype-Nano доступна")
        logger.info(f"{WARN_MARKER} Для полной загрузки требуется ~3GB VRAM или CPU режим")
        
        return True, {
            'model_name': model_name,
            'tokenizer_size': len(tokenizer),
            'status': 'available'
        }
        
    except Exception as e:
        logger.error(f"{ERROR_MARKER} Ошибка при тестировании Cotype: {str(e)}")
        return False, {'error': str(e)}


def test_tpro():
    """Тест загрузки T-Pro-it-1.0"""
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
        
        # Проверка конфигурации модели
        logger.info("Проверка конфигурации модели...")
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


def main():
    """Главная функция для запуска всех тестов"""
    logger.info("=" * 60)
    logger.info("НАЧАЛО ТЕСТИРОВАНИЯ LLM МОДЕЛЕЙ")
    logger.info("=" * 60)
    
    # Информация о системе
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
    
    # Тест GigaChat
    try:
        success, info = test_gigachat()
        results['gigachat'] = {'success': success, 'info': info}
    except Exception as e:
        logger.error(f"Критическая ошибка при тестировании GigaChat: {str(e)}")
        results['gigachat'] = {'success': False, 'error': str(e)}
    
    logger.info("")
    
    # Тест Cotype
    try:
        success, info = test_cotype()
        results['cotype'] = {'success': success, 'info': info}
    except Exception as e:
        logger.error(f"Критическая ошибка при тестировании Cotype: {str(e)}")
        results['cotype'] = {'success': False, 'error': str(e)}
    
    logger.info("")
    
    # Тест T-Pro
    try:
        success, info = test_tpro()
        results['tpro'] = {'success': success, 'info': info}
    except Exception as e:
        logger.error(f"Критическая ошибка при тестировании T-Pro: {str(e)}")
        results['tpro'] = {'success': False, 'error': str(e)}
    
    # Итоговый отчет
    logger.info("")
    logger.info("=" * 60)
    logger.info("ИТОГОВЫЙ ОТЧЕТ")
    logger.info("=" * 60)
    
    for model_name, result in results.items():
        status = f"{OK_MARKER} УСПЕШНО" if result['success'] else f"{ERROR_MARKER} ОШИБКА"
        logger.info(f"{model_name.upper()}: {status}")
        if result['success'] and 'info' in result:
            logger.info(f"  Модель: {result['info'].get('model_name', 'N/A')}")
            logger.info(f"  Статус: {result['info'].get('status', 'N/A')}")
    
    # Сохранение результатов
    import json
    results_file = Path('ml/models/test_results.json')
    results_file.parent.mkdir(parents=True, exist_ok=True)
    
    results_summary = {
        'timestamp': datetime.now().isoformat(),
        'system_info': sys_info,
        'results': results
    }
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results_summary, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\nРезультаты сохранены в: {results_file}")
    
    # Проверка успешности всех тестов
    all_success = all(r['success'] for r in results.values())
    
    if all_success:
        logger.info(f"\n{OK_MARKER} ВСЕ МОДЕЛИ УСПЕШНО ПРОТЕСТИРОВАНЫ")
        return 0
    else:
        logger.warning(f"\n{WARN_MARKER} НЕКОТОРЫЕ МОДЕЛИ НЕ ПРОШЛИ ТЕСТИРОВАНИЕ")
        return 1


if __name__ == "__main__":
    sys.exit(main())
