"""
Скрипт для бенчмарка всех 3 LLM моделей:
- GigaChat3-10B-A1.8B
- Cotype-Nano
- T-Pro-it-1.0

Собирает метрики: время ответа, качество ответа, успешность, стоимость
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import re

# Добавляем путь к корню проекта для импорта
sys.path.insert(0, str(Path(__file__).parent.parent))

# Увеличение таймаутов для Hugging Face
os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '300'  # 5 минут
os.environ['HF_HUB_DOWNLOAD_RETRY'] = '3'

# Проверка зависимостей
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    from huggingface_hub import snapshot_download
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("WARNING: transformers не установлен. Будет использован mock режим.")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ml/benchmarks/benchmark.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Тестовые данные - магазины с координатами
TEST_LOCATIONS = [
    {"id": "store-1", "name": "Магазин Центральный", "lat": 55.7558, "lon": 37.6173, "address": "Красная площадь, 1"},
    {"id": "store-2", "name": "Магазин Арбат", "lat": 55.7489, "lon": 37.6160, "address": "Арбат, 15"},
    {"id": "store-3", "name": "Магазин Тверская", "lat": 55.7520, "lon": 37.6156, "address": "Тверская, 10"},
    {"id": "store-4", "name": "Магазин Парк Культуры", "lat": 55.7358, "lon": 37.5933, "address": "Крымский вал, 9"},
    {"id": "store-5", "name": "Магазин Сокольники", "lat": 55.7904, "lon": 37.6794, "address": "Сокольническая площадь, 1"},
    {"id": "store-6", "name": "Магазин Измайлово", "lat": 55.7879, "lon": 37.7704, "address": "Измайловский проспект, 73"},
    {"id": "store-7", "name": "Магазин ВДНХ", "lat": 55.8294, "lon": 37.6283, "address": "Проспект Мира, 119"},
    {"id": "store-8", "name": "Магазин Останкино", "lat": 55.8197, "lon": 37.6117, "address": "1-я Останкинская, 55"},
]

# Тестовые промпты для бенчмарка
TEST_PROMPTS = [
    {
        "task": "route_planning",
        "prompt": "Планирую посетить магазины: Магазин Центральный, Магазин Арбат, Магазин Тверская. "
                  "Начну с Красной площади. Предложи оптимальный маршрут с учетом расстояний между точками.",
        "expected_keywords": ["маршрут", "расстояние", "оптимальный", "порядок"]
    },
    {
        "task": "store_info",
        "prompt": "Расскажи о магазинах в районе Сокольников и ВДНХ. Какие из них ближе друг к другу?",
        "expected_keywords": ["магазин", "расстояние", "ближе", "координаты"]
    },
    {
        "task": "logistics",
        "prompt": "Нужно доставить товары в 5 магазинов: Центральный, Арбат, Тверская, Парк Культуры, Сокольники. "
                  "Начни с Центрального. Составь план доставки с минимальным пробегом.",
        "expected_keywords": ["план", "доставка", "маршрут", "пробег", "порядок"]
    },
    {
        "task": "analysis",
        "prompt": "Проанализируй расположение всех магазинов. Какие районы покрыты лучше всего? "
                  "Где есть пробелы в покрытии?",
        "expected_keywords": ["анализ", "расположение", "покрытие", "район"]
    },
    {
        "task": "optimization",
        "prompt": "Если нужно открыть новый магазин для лучшего покрытия города, "
                  "где бы ты его разместил? Объясни свой выбор.",
        "expected_keywords": ["новый", "магазин", "размещение", "покрытие", "выбор"]
    }
]


class ModelBenchmark:
    """Класс для бенчмарка одной модели"""
    
    def __init__(self, model_name: str, model_id: str, use_mock: bool = False):
        self.model_name = model_name
        self.model_id = model_id
        self.use_mock = use_mock or not TRANSFORMERS_AVAILABLE
        self.tokenizer = None
        self.model = None
        self.loaded = False
        
    def load_model(self, timeout_seconds: int = 60):
        """Загрузка модели (или использование mock)"""
        if self.use_mock:
            logger.info(f"[MOCK] Модель {self.model_id} будет использовать mock режим")
            self.loaded = True
            return True
            
        try:
            logger.info(f"Загрузка модели {self.model_id}...")
            logger.info(f"Это может занять несколько минут при первой загрузке...")
            
            # Загрузка токенизатора с увеличенным таймаутом
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.model_name, 
                    trust_remote_code=True,
                    timeout=300  # 5 минут таймаут
                )
            except Exception as e:
                logger.warning(f"[WARN] Не удалось загрузить токенизатор: {e}")
                logger.info(f"Переключение на mock режим для {self.model_id}")
                self.use_mock = True
                self.loaded = True
                return False
            
            # Пытаемся загрузить модель
            if torch.cuda.is_available():
                try:
                    self.model = AutoModelForCausalLM.from_pretrained(
                        self.model_name,
                        torch_dtype=torch.float16 if self.model_id != "gigachat" else torch.bfloat16,
                        device_map="auto",
                        trust_remote_code=True,
                        low_cpu_mem_usage=True
                    )
                    logger.info(f"[OK] Модель {self.model_id} загружена на GPU")
                except Exception as e:
                    logger.warning(f"[WARN] Не удалось загрузить на GPU: {e}")
                    # Для маленьких моделей пробуем CPU
                    if self.model_id == "cotype":
                        try:
                            logger.info(f"Попытка загрузки {self.model_id} на CPU...")
                            logger.info(f"ВНИМАНИЕ: Загрузка может занять 5-15 минут и потребовать ~3GB RAM")
                            logger.info(f"Если загрузка слишком долгая, нажмите Ctrl+C и используйте --mock")
                            
                            self.model = AutoModelForCausalLM.from_pretrained(
                                self.model_name,
                                torch_dtype=torch.float32,
                                device_map="cpu",
                                trust_remote_code=True,
                                low_cpu_mem_usage=True,
                                timeout=600  # 10 минут для загрузки модели
                            )
                            logger.info(f"[OK] Модель {self.model_id} загружена на CPU")
                        except KeyboardInterrupt:
                            logger.warning(f"[WARN] Загрузка прервана пользователем. Используется mock.")
                            self.use_mock = True
                        except Exception as e2:
                            logger.warning(f"[WARN] Не удалось загрузить на CPU: {e2}. Используется mock.")
                            self.use_mock = True
                    else:
                        logger.warning(f"[WARN] Используется mock для {self.model_id}")
                        self.use_mock = True
            else:
                # Для маленьких моделей пробуем CPU
                if self.model_id == "cotype":
                    try:
                        logger.info(f"CUDA недоступна. Попытка загрузки {self.model_id} на CPU...")
                        logger.info(f"ВНИМАНИЕ: Загрузка может занять 5-15 минут и потребовать ~3GB RAM")
                        logger.info(f"Если загрузка слишком долгая, нажмите Ctrl+C и используйте --mock")
                        
                        self.model = AutoModelForCausalLM.from_pretrained(
                            self.model_name,
                            torch_dtype=torch.float32,
                            device_map="cpu",
                            trust_remote_code=True,
                            low_cpu_mem_usage=True,
                            timeout=600  # 10 минут для загрузки модели
                        )
                        logger.info(f"[OK] Модель {self.model_id} загружена на CPU")
                    except KeyboardInterrupt:
                        logger.warning(f"[WARN] Загрузка прервана пользователем. Используется mock.")
                        self.use_mock = True
                    except Exception as e:
                        logger.warning(f"[WARN] Не удалось загрузить на CPU: {e}. Используется mock.")
                        self.use_mock = True
                else:
                    logger.warning(f"[WARN] CUDA недоступна. Используется mock для {self.model_id}")
                    self.use_mock = True
                
            self.loaded = True
            return True
            
        except Exception as e:
            error_msg = str(e)
            # Проверка на таймауты и сетевые ошибки
            if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                logger.error(f"[ERROR] Таймаут при загрузке модели {self.model_id}")
                logger.info(f"Возможные причины: медленное интернет-соединение или проблемы с Hugging Face")
                logger.info(f"Переключение на mock режим для {self.model_id}")
            elif "connection" in error_msg.lower() or "network" in error_msg.lower():
                logger.error(f"[ERROR] Проблемы с сетью при загрузке модели {self.model_id}")
                logger.info(f"Переключение на mock режим для {self.model_id}")
            else:
                logger.error(f"[ERROR] Ошибка загрузки модели {self.model_id}: {e}")
                logger.info(f"Переключение на mock режим для {self.model_id}")
            
            self.use_mock = True
            self.loaded = True
            return False
    
    def generate_response(self, prompt: str, max_tokens: int = 200) -> Dict[str, Any]:
        """Генерация ответа модели"""
        start_time = time.time()
        success = False
        response_text = ""
        error = None
        
        try:
            if self.use_mock:
                # Mock ответ для тестирования
                response_text = self._generate_mock_response(prompt)
                success = True
            else:
                if self.model is None or self.tokenizer is None:
                    raise ValueError("Модель не загружена")
                
                # Форматирование промпта
                if self.model_id == "gigachat":
                    messages = [{"role": "user", "content": prompt}]
                    input_tensor = self.tokenizer.apply_chat_template(
                        messages,
                        add_generation_prompt=True,
                        return_tensors="pt"
                    ).to(self.model.device)
                else:
                    input_tensor = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
                
                # Генерация
                with torch.no_grad():
                    outputs = self.model.generate(
                        input_tensor,
                        max_new_tokens=max_tokens,
                        do_sample=True,
                        temperature=0.7,
                        top_p=0.9,
                        pad_token_id=self.tokenizer.eos_token_id
                    )
                
                # Декодирование
                if self.model_id == "gigachat":
                    response_text = self.tokenizer.decode(
                        outputs[0][input_tensor.shape[1]:],
                        skip_special_tokens=True
                    )
                else:
                    response_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                
                success = True
                
        except Exception as e:
            error = str(e)
            logger.error(f"Ошибка генерации для {self.model_id}: {e}")
            response_text = f"[ERROR: {error}]"
        
        response_time_ms = (time.time() - start_time) * 1000
        
        return {
            "response": response_text,
            "response_time_ms": response_time_ms,
            "success": success,
            "error": error
        }
    
    def _generate_mock_response(self, prompt: str) -> str:
        """Генерация mock ответа для тестирования (разные для каждой модели)"""
        # Разные стили ответов для разных моделей
        base_response = ""
        
        if "маршрут" in prompt.lower() or "доставка" in prompt.lower():
            if self.model_id == "gigachat":
                base_response = """Оптимальный маршрут от GigaChat:
1. Начните с Магазина Центральный (Красная площадь, 55.7558, 37.6173)
2. Затем посетите Магазин Тверская (расстояние ~1.2 км, 55.7520, 37.6156)
3. Завершите в Магазине Арбат (расстояние ~0.8 км, 55.7489, 37.6160)

Общий пробег: примерно 2.5 км. Это оптимальный порядок для минимизации времени в пути."""
            elif self.model_id == "cotype":
                base_response = """Маршрут от Cotype:
Центральный → Тверская → Арбат. Общее расстояние около 2.5 км. 
Рекомендую начать с центрального магазина для экономии времени."""
            else:  # tpro
                base_response = """T-Pro рекомендует маршрут:
1. Центральный магазин (стартовая точка)
2. Тверская (1.2 км от центра)
3. Арбат (0.8 км от Тверской)
Минимальный пробег: 2.5 км"""
        
        elif "анализ" in prompt.lower() or "расположение" in prompt.lower():
            if self.model_id == "gigachat":
                base_response = """Анализ расположения магазинов (GigaChat):
- Центральный район: хорошо покрыт (3 магазина: Центральный, Арбат, Тверская)
- Северо-восток: покрытие среднее (2 магазина: ВДНХ, Останкино)
- Юго-запад: требуется дополнительное покрытие (только Парк Культуры)

Рекомендация: открыть новый магазин в районе Юго-Запада для улучшения покрытия."""
            elif self.model_id == "cotype":
                base_response = """Анализ покрытия: центральный район имеет 3 магазина, 
северо-восток - 2, юго-запад нуждается в дополнительных точках."""
            else:  # tpro
                base_response = """T-Pro анализ: 
Центральный район: 3 точки (отлично)
Северо-восток: 2 точки (хорошо)
Юго-запад: 1 точка (требует улучшения)"""
        
        elif "новый магазин" in prompt.lower():
            if self.model_id == "gigachat":
                base_response = """Для нового магазина рекомендую район между Парком Культуры и Сокольниками.
Координаты: примерно 55.76, 37.60. Это обеспечит:
- Покрытие пробела в сети
- Доступность для жителей юго-запада
- Оптимальное расстояние до других точек"""
            elif self.model_id == "cotype":
                base_response = """Новый магазин: рекомендую координаты 55.76, 37.60 
для улучшения покрытия юго-западного района."""
            else:  # tpro
                base_response = """T-Pro рекомендует разместить новый магазин 
в точке 55.76, 37.60 для оптимизации сети."""
        
        else:
            if self.model_id == "gigachat":
                base_response = f"GigaChat: Промпт содержит информацию о {len(TEST_LOCATIONS)} магазинах. " \
                               f"Рекомендую использовать систему навигации для построения оптимального маршрута."
            elif self.model_id == "cotype":
                base_response = f"Cotype: Доступно {len(TEST_LOCATIONS)} магазинов. " \
                               f"Используйте навигацию для планирования маршрута."
            else:  # tpro
                base_response = f"T-Pro: В системе {len(TEST_LOCATIONS)} магазинов. " \
                               f"Для оптимального маршрута используйте навигационные сервисы."
        
        return base_response
    
    def calculate_quality_score(self, response: str, prompt: str, expected_keywords: List[str]) -> float:
        """Расчет качества ответа (0-100)"""
        if not response or response.startswith("[ERROR"):
            return 0.0
        
        score = 0.0
        
        # Базовая оценка за длину ответа (не слишком короткий, не слишком длинный)
        length = len(response)
        if 50 <= length <= 1000:
            score += 20.0
        elif length < 50:
            score += 10.0
        else:
            score += 15.0
        
        # Наличие ключевых слов
        response_lower = response.lower()
        found_keywords = sum(1 for kw in expected_keywords if kw.lower() in response_lower)
        keyword_score = (found_keywords / len(expected_keywords)) * 30.0 if expected_keywords else 0
        score += keyword_score
        
        # Структурированность (наличие списков, цифр, структуры)
        has_structure = bool(re.search(r'\d+\.|•|—|:', response))
        if has_structure:
            score += 15.0
        
        # Отсутствие очевидных ошибок
        has_errors = bool(re.search(r'\[ERROR|None|undefined|NaN', response, re.IGNORECASE))
        if not has_errors:
            score += 15.0
        
        # Релевантность (упоминание магазинов, координат, маршрутов)
        relevant_terms = ["магазин", "маршрут", "расстояние", "координат", "план", "доставка"]
        relevant_count = sum(1 for term in relevant_terms if term in response_lower)
        relevance_score = min(relevant_count / 3.0, 1.0) * 20.0
        score += relevance_score
        
        return min(score, 100.0)


def run_benchmark(
    num_iterations: int = 5,
    test_data: Optional[List[Dict[str, Any]]] = None,
    use_mock: bool = False
) -> Dict[str, Any]:
    """
    Запуск бенчмарка на всех моделях
    
    Args:
        num_iterations: Количество итераций тестирования на каждую модель
        test_data: Тестовые данные (промпты). Если None, используются TEST_PROMPTS
        use_mock: Использовать mock режим (для тестирования без загрузки моделей)
    
    Returns:
        Словарь с результатами бенчмарка
    """
    logger.info("=" * 70)
    logger.info("НАЧАЛО БЕНЧМАРКА LLM МОДЕЛЕЙ")
    logger.info("=" * 70)
    
    if test_data is None:
        test_data = TEST_PROMPTS
    
    # Инициализация моделей
    models = {
        "gigachat": ModelBenchmark(
            "ai-sage/GigaChat3-10B-A1.8B",
            "gigachat",
            use_mock=use_mock
        ),
        "cotype": ModelBenchmark(
            "MTSAIR/Cotype-Nano",
            "cotype",
            use_mock=use_mock
        ),
        "tpro": ModelBenchmark(
            "t-tech/T-pro-it-1.0",
            "tpro",
            use_mock=use_mock
        )
    }
    
    # Загрузка моделей
    logger.info("\nЗагрузка моделей...")
    for model_id, model in models.items():
        model.load_model()
        time.sleep(1)  # Небольшая пауза между загрузками
    
    # Результаты бенчмарка
    benchmark_results = {
        "timestamp": datetime.now().isoformat(),
        "num_iterations": num_iterations,
        "test_data_count": len(test_data),
        "models": {}
    }
    
    # Бенчмарк для каждой модели
    for model_id, model in models.items():
        logger.info("\n" + "=" * 70)
        logger.info(f"БЕНЧМАРК МОДЕЛИ: {model_id.upper()}")
        logger.info("=" * 70)
        
        model_results = {
            "model_name": model.model_name,
            "model_id": model_id,
            "use_mock": model.use_mock,
            "iterations": []
        }
        
        total_response_time = 0.0
        total_quality_score = 0.0
        successful_responses = 0
        total_cost_rub = 0.0
        
        # Итерации тестирования
        for iteration in range(num_iterations):
            logger.info(f"\nИтерация {iteration + 1}/{num_iterations}")
            
            iteration_results = []
            
            for test_idx, test_item in enumerate(test_data):
                prompt = test_item["prompt"]
                expected_keywords = test_item.get("expected_keywords", [])
                
                logger.info(f"  Тест {test_idx + 1}/{len(test_data)}: {test_item['task']}")
                
                # Генерация ответа
                result = model.generate_response(prompt, max_tokens=200)
                
                # Расчет качества
                quality_score = model.calculate_quality_score(
                    result["response"],
                    prompt,
                    expected_keywords
                )
                
                # Расчет стоимости (примерные значения для разных моделей)
                cost_rub = 0.0
                if not model.use_mock:
                    # Примерные цены (нужно уточнить для реальных API)
                    if model_id == "gigachat":
                        cost_rub = result["response_time_ms"] * 0.0001  # Примерно 0.1 руб/сек
                    elif model_id == "cotype":
                        cost_rub = result["response_time_ms"] * 0.00005  # Примерно 0.05 руб/сек
                    elif model_id == "tpro":
                        cost_rub = result["response_time_ms"] * 0.00008  # Примерно 0.08 руб/сек
                
                iteration_result = {
                    "test_id": test_idx,
                    "task": test_item["task"],
                    "response_time_ms": round(result["response_time_ms"], 2),
                    "quality_score": round(quality_score, 2),
                    "success": result["success"],
                    "cost_rub": round(cost_rub, 4),
                    "response_length": len(result["response"]),
                    "error": result.get("error")
                }
                
                iteration_results.append(iteration_result)
                
                # Накопление статистики
                if result["success"]:
                    successful_responses += 1
                    total_response_time += result["response_time_ms"]
                    total_quality_score += quality_score
                    total_cost_rub += cost_rub
                
                logger.info(f"    Время: {result['response_time_ms']:.2f} мс, "
                          f"Качество: {quality_score:.2f}, "
                          f"Успех: {result['success']}")
            
            model_results["iterations"].append(iteration_results)
        
        # Расчет итоговых метрик
        total_tests = num_iterations * len(test_data)
        success_rate = (successful_responses / total_tests * 100) if total_tests > 0 else 0
        
        avg_response_time = (total_response_time / successful_responses) if successful_responses > 0 else 0
        avg_quality_score = (total_quality_score / successful_responses) if successful_responses > 0 else 0
        
        model_results["metrics"] = {
            "response_time_ms": round(avg_response_time, 2),
            "quality_score": round(avg_quality_score, 2),
            "success_rate": round(success_rate, 2),
            "cost_rub": round(total_cost_rub, 4),
            "total_tests": total_tests,
            "successful_tests": successful_responses
        }
        
        benchmark_results["models"][model_id] = model_results
        
        logger.info(f"\nИтоги для {model_id}:")
        logger.info(f"  Среднее время ответа: {avg_response_time:.2f} мс")
        logger.info(f"  Среднее качество: {avg_quality_score:.2f}/100")
        logger.info(f"  Успешность: {success_rate:.2f}%")
        logger.info(f"  Общая стоимость: {total_cost_rub:.4f} руб")
    
    # Сохранение результатов
    results_file = Path("ml/benchmarks/results.json")
    results_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(benchmark_results, f, indent=2, ensure_ascii=False)
    
    logger.info("\n" + "=" * 70)
    logger.info("БЕНЧМАРК ЗАВЕРШЕН")
    logger.info("=" * 70)
    logger.info(f"Результаты сохранены в: {results_file}")
    
    # Итоговая сводка
    logger.info("\nИТОГОВАЯ СВОДКА:")
    for model_id, model_data in benchmark_results["models"].items():
        metrics = model_data["metrics"]
        logger.info(f"\n{model_id.upper()}:")
        logger.info(f"  Время ответа: {metrics['response_time_ms']:.2f} мс")
        logger.info(f"  Качество: {metrics['quality_score']:.2f}/100")
        logger.info(f"  Успешность: {metrics['success_rate']:.2f}%")
        logger.info(f"  Стоимость: {metrics['cost_rub']:.4f} руб")
    
    return benchmark_results


def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Бенчмарк LLM моделей")
    parser.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="Количество итераций тестирования (по умолчанию: 5)"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Использовать mock режим (без загрузки моделей)"
    )
    
    args = parser.parse_args()
    
    # Запуск бенчмарка
    results = run_benchmark(
        num_iterations=args.iterations,
        use_mock=args.mock
    )
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
