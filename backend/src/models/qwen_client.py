import asyncio
import json
import logging
from datetime import datetime
from time import time
from typing import (
    Dict,
    List,
)

try:
    from llama_cpp import Llama
except ImportError:
    raise ImportError(
        "Please install llama-cpp-python: pip install llama-cpp-python",
    )

from src.config import settings
from src.models.exceptions import (
    QwenError,
    QwenServerError,
    QwenTimeoutError,
    QwenValidationError,
)
from src.models.llm_client import LLMClient
from src.models.geo_utils import (
    build_constraints_text,
    build_nearest_neighbors,
    compute_distance_matrix,
    detect_region_info,
    estimate_fuel_cost,
    format_locations_compact,
    format_nearest_neighbors,
)
from src.models.schemas import (
    Location,
    Route,
)

logger = logging.getLogger("qwen_client")


class QwenClient(LLMClient):
    _llm = None

    def __init__(self):
        self.model_name = settings.qwen_model_id
        self.timeout = 120
        try:
            self.model_path = settings.get_model_path(settings.qwen_model_id)
        except FileNotFoundError as e:
            logger.error(str(e))
            self.model_path = None

    def _get_generator(self):
        """Lazy Loading модели через llama.cpp."""
        if QwenClient._llm is None:
            if not self.model_path:
                raise QwenServerError(
                    f"Model file for {self.model_name} not found.",
                )

            try:
                logger.info(f"Loading Qwen GGUF from {self.model_path}...")
                QwenClient._llm = Llama(
                    model_path=self.model_path,
                    n_threads=4,
                    n_gpu_layers=0,
                    n_ctx=2048,
                    n_batch=512,
                    verbose=True,
                )
                logger.info("Qwen GGUF model loaded successfully.")
            except Exception as e:
                logger.error(f"Critical error loading Qwen GGUF: {e}")
                raise QwenServerError(f"Failed to load local model: {e}")
        return QwenClient._llm

    async def generate_route(
        self,
        locations: List[Location],
        constraints: Dict = None,
    ) -> Route:
        if not locations:
            logger.error("Validation failed: locations list is empty")
            raise QwenValidationError("Locations list is empty")

        start_time = time()
        logger.debug(
            "Request sent to Qwen GGUF",
            extra={
                "locations_count": len(locations),
                "constraints": constraints,
            },
        )

        max_retries = 3
        backoff_factor = 1

        locations_data = [loc.model_dump() for loc in locations]

        for attempt in range(1, max_retries + 2):
            try:
                response_text = await self._run_inference(
                    locations_data,
                    constraints,
                )
                logger.info(f"RAW MODEL RESPONSE (Attempt {attempt}):\n{response_text}")
                print(response_text)
                result = self._parse_response(response_text, locations)

                duration = time() - start_time
                if duration > 10.0:
                    logger.warning(f"Slow generation: {duration:.2f}s")

                logger.info(
                    "Route generated successfully",
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
                        f"Error attempt {attempt}/{max_retries}: "
                        f"{type(e).__name__}. Retry in {sleep_time}s",
                    )
                    await asyncio.sleep(sleep_time)
                else:
                    logger.error("All generation attempts exhausted.")
                    if isinstance(e, QwenError):
                        raise e
                    raise QwenServerError(
                        f"Local generation failed: {e}",
                    )

    async def _run_inference(
        self,
        locations_data: List[Dict],
        constraints: Dict,
    ) -> str:
        """Запуск инференса в отдельном потоке."""
        llm = self._get_generator()
        prompt = self._construct_prompt(locations_data, constraints)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a route optimizer. "
                    "Output ONLY valid JSON, no text."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        loop = asyncio.get_event_loop()
        try:
            output = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: llm.create_chat_completion(
                        messages=messages,
                        max_tokens=512,
                        temperature=0.1,
                        stop=["<|im_end|>"],
                    ),
                ),
                timeout=self.timeout,
            )

            return output["choices"][0]["message"]["content"]

        except asyncio.TimeoutError:
            raise QwenTimeoutError(
                f"Generation exceeded timeout of {self.timeout}s",
            )
        except Exception as e:
            raise QwenServerError(f"Inference error: {e}")

    def _construct_prompt(
        self,
        locations: List[Dict],
        constraints: Dict,
    ) -> str:
        region = detect_region_info(locations)
        dm = compute_distance_matrix(locations)
        nn = build_nearest_neighbors(dm, k=3)

        locations_text = format_locations_compact(locations)
        nn_text = format_nearest_neighbors(locations, nn)
        constraints_text = build_constraints_text(constraints)

        fuel_rate = (constraints or {}).get("fuel_rate", 7.0)
        speed = 25 if region["classification"] == "urban" else 40

        return (
            f"LOCATIONS ({len(locations)} points, "
            f"{region['classification']} area, "
            f"{region['area_km2']}km2):\n"
            f"{locations_text}\n\n"
            f"DISTANCES (nearest neighbors):\n{nn_text}\n\n"
            f"RULES: {constraints_text}\n"
            f"Order by priority (high=A>B>C>D). Minimize total km.\n"
            f"Speed: {speed}km/h + 15min per visit. "
            f"Cost = distance * {fuel_rate} rub/km.\n\n"
            f"OUTPUT: single JSON, no markdown:\n"
            f'{{"route_id":"id","locations_sequence":["id1","id2"],'
            f'"total_distance_km":0.0,"total_time_hours":0.0,'
            f'"total_cost_rub":0.0,'
            f'"model_used":"{self.model_name}",'
            f'"created_at":"{datetime.now().isoformat()}"}}'
        )

    def _parse_response(
        self,
        text_content: str,
        original_locations: List[Location],
    ) -> Route:
        try:
            # Очистка markdown блоков, если модель их добавила
            clean_text = text_content.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]

            json_start = clean_text.find("{")
            json_end = clean_text.rfind("}") + 1
            if json_start == -1:
                raise ValueError("No JSON object found in response")

            data = json.loads(clean_text[json_start:json_end])

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
                f"Parsing error: {e}. Text: {text_content}",
            )
            raise QwenServerError(f"Route Validation Error: {str(e)}")

    async def analyze_metrics(self, data: Dict) -> str:
        return "Not implemented"

    async def health_check(self) -> bool:
        return QwenClient._llm is not None
