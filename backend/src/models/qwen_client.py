import asyncio
import json
import logging
from datetime import datetime
from time import time
from typing import Dict, List

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

from src.config import settings
from src.models.exceptions import (
    QwenError,
    QwenServerError,
    QwenTimeoutError,
    QwenValidationError,
)
from src.models.llm_client import LLMClient
from src.models.schemas import Location, Route


logger = logging.getLogger("qwen_client")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class QwenClient(LLMClient):
    _generator = None

    def __init__(self):
        self.model_name = settings.qwen_model_id
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.timeout = 30

    def _get_generator(self):
        """Загрузка модели один раз при первом вызове"""
        if QwenClient._generator is None:
            try:
                logger.info(
                    f"Инициализация локальной модели {self.model_name} "
                    f"на {self.device}...",
                )
                tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    dtype=(torch.float32 if self.device == "cpu" else torch.float16),
                    device_map="auto",
                    low_cpu_mem_usage=True,
                    load_in_8bit=True,
                    trust_remote_code=True,
                )
                QwenClient._generator = pipeline(
                    "text-generation",
                    model=model,
                    tokenizer=tokenizer,
                )
                logger.info("Локальная модель успешно загружена в память.")
            except Exception as e:
                logger.error(f"Критическая ошибка при загрузке модели: {e}")
                raise QwenServerError(f"Failed to load local model: {e}")
        return QwenClient._generator

    async def generate_route(
        self,
        locations: List[Location],
        constraints: Dict = None,
    ) -> Route:
        if not locations:
            logger.error("Валидация провалена: список локаций пуст")
            raise QwenValidationError("Список локаций пуст")

        start_time = time()
        logger.debug(
            "Запрос отправлен в локальную LLM",
            extra={
                "locations_count": len(locations),
                "constraints": constraints,
            },
        )

        max_retries = 3
        backoff_factor = 1

        for attempt in range(1, max_retries + 2):
            try:
                response_text = await self._run_inference(locations, constraints)

                result = self._parse_response(response_text, locations)

                duration = time() - start_time
                if duration > 10.0:
                    logger.warning(f"Медленная генерация: {duration:.2f}s")

                logger.info(
                    "Маршрут успешно сгенерирован",
                    extra={
                        "duration": duration,
                        "distance": result.total_distance_km,
                    },
                )
                return result

            except Exception as e:
                if attempt <= max_retries:
                    sleep_time = backoff_factor * (2 ** (attempt - 1))
                    logger.error(
                        f"Ошибка попытки {attempt}/{max_retries}: "
                        f"{type(e).__name__}. Retry in {sleep_time}s",
                    )
                    await asyncio.sleep(sleep_time)
                else:
                    logger.error("Все попытки генерации исчерпаны. Fallback required.")
                    if isinstance(e, QwenError):
                        raise e
                    raise QwenServerError(f"Local generation failed after retries: {e}")

    async def _run_inference(self, locations: List[Location], constraints: Dict) -> str:
        """Обертка над синхронным pipeline"""
        generator = self._get_generator()
        prompt = self._construct_prompt(
            [loc.model_dump() for loc in locations],
            constraints,
        )

        messages = [
            {
                "role": "system",
                "content": "You are a logistics expert. " "Return ONLY valid JSON.",
            },
            {"role": "user", "content": prompt},
        ]

        full_prompt = generator.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        loop = asyncio.get_event_loop()
        try:
            outputs = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: generator(
                        full_prompt,
                        max_new_tokens=128,
                        do_sample=False,
                        num_beams=1,
                        temperature=0.1,
                    ),
                ),
                timeout=self.timeout,
            )

            raw_text = outputs[0]["generated_text"]
            if "<|im_start|>assistant" in raw_text:
                return raw_text.split("<|im_start|>assistant")[-1].strip()
            return raw_text

        except asyncio.TimeoutError:
            raise QwenTimeoutError(f"Generation exceeded timeout of {self.timeout}s")

    def _construct_prompt(self, locations: List[Dict], constraints: Dict) -> str:
        locations_json = json.dumps(locations, ensure_ascii=False)
        return f"""Optimize route for: {locations_json}
        You are logistic expert. Use your skills to generate proper route.
        Points with high priority should be visited first.
        Total cost in rubles would be
        calculated as petrol prices.
        It's all depends on location (town in Russia).
        You should search for petrol price for current region
        (you can get what's location
        by analyzing address).
        Return ONLY JSON with these exact keys:
        {{
            "route_id": "string",
            "locations_sequence": ["id1", "id2", "id3", ...],
            "total_distance_km": float,
            "total_time_hours": float,
            "total_cost_rub": float,
            "model_used": "qwen-local",
            "created_at": "{datetime.now().isoformat()}"
        }}"""

    def _parse_response(
        self,
        text_content: str,
        original_locations: List[Location],
    ) -> Route:
        try:
            json_start = text_content.find("{")
            json_end = text_content.rfind("}") + 1
            data = json.loads(text_content[json_start:json_end])

            def to_float(val):
                try:
                    return float(val) if val is not None else 0.0
                except Exception:
                    return 0.0

            return Route(
                ID=str(data.get("route_id", f"route-{int(time())}")),
                name=f"Оптимизированный маршрут ({self.model_name})",
                locations=original_locations,
                total_distance_km=to_float(data.get("total_distance_km")),
                total_time_hours=to_float(data.get("total_time_hours")),
                total_cost_rub=to_float(data.get("total_cost_rub")),
                model_used=str(data.get("model_used", self.model_name)),
                created_at=data.get("created_at") or datetime.now(),
            )
        except Exception as e:
            logger.error(
                f"Ошибка парсинга или валидации: {e}. " f"Текст: {text_content}",
            )
            raise QwenServerError(f"Route Validation Error: {str(e)}")

    async def analyze_metrics(self, data: Dict) -> str:
        return "Not implemented"

    async def health_check(self) -> bool:
        return torch.cuda.is_available() or self.device == "cpu"
