import asyncio
import json
import logging
import uuid
from datetime import datetime
from time import time
from typing import Dict, List

try:
    from llama_cpp import Llama
except ImportError as exc:
    raise ImportError(
        "Please install llama-cpp-python: pip install llama-cpp-python",
    ) from exc

from src.config import settings
from src.models.exceptions import (
    LlamaServerError,
    LlamaValidationError,
)
from src.models.geo_utils import (
    build_constraints_text,
    build_nearest_neighbors,
    compute_distance_matrix,
    detect_region_info,
    format_locations_compact,
    format_nearest_neighbors,
)
from src.models.llm_client import LLMClient
from src.models.schemas import (
    Location,
    Route,
)

logger = logging.getLogger("llama_client")


class LlamaClient(LLMClient):
    _llm = None

    def __init__(self):
        self.model_name = settings.llama_model_id
        self.timeout = 120
        try:
            self.model_path = settings.get_model_path(
                settings.llama_model_id,
            )
        except FileNotFoundError as exc:
            logger.error(str(exc))
            self.model_path = None

    def _get_generator(self):
        """Lazy loading модели через llama.cpp."""
        if LlamaClient._llm is None:
            if not self.model_path:
                raise LlamaServerError(
                    f"Model file {self.model_name} "
                    "not found in project directories.",
                )

            try:
                logger.info(
                    "Loading GGUF model from %s...",
                    self.model_path,
                )
                LlamaClient._llm = Llama(
                    model_path=self.model_path,
                    n_threads=8,
                    n_threads_batch=8,
                    n_gpu_layers=-1,
                    n_batch=512,
                    n_ctx=49152,  # 48K — достаточно для 50 точек (~40K токенов)
                    verbose=True,
                )
                logger.info("Llama GGUF model loaded successfully.")
            except Exception as exc:
                logger.error(
                    "Critical error loading GGUF model: %s",
                    exc,
                )
                raise LlamaServerError(
                    f"Failed to load GGUF model: {exc}",
                ) from exc

        return LlamaClient._llm

    async def generate_route(
        self,
        locations: List[Location],
        constraints: Dict | None = None,
    ) -> Route:
        if not locations:
            raise LlamaValidationError("Locations list is empty")

        start_time = time()
        max_retries = 3

        locations_data = [loc.model_dump() for loc in locations]

        for attempt in range(1, max_retries + 2):
            try:
                response_text = await self._run_inference(
                    locations_data,
                    constraints,
                )

                logger.info(
                    "RAW MODEL RESPONSE (Attempt %s):\n%s",
                    attempt,
                    response_text,
                )

                result = self._parse_response(
                    response_text,
                    locations,
                )

                duration = time() - start_time
                if duration > 5.0:
                    logger.warning(
                        "Llama slow response: %.2fs",
                        duration,
                    )

                return result

            except Exception as exc:
                if attempt <= max_retries:
                    logger.warning(
                        "Retry %s/%s due to: %s",
                        attempt,
                        max_retries,
                        exc,
                    )
                else:
                    logger.error("All retries exhausted.")
                    raise LlamaServerError(
                        f"Generation failed: {exc}",
                    ) from exc

    async def _run_inference(
        self,
        locations_data: List[Dict],
        constraints: Dict | None,
    ) -> str:
        llm = self._get_generator()

        system_prompt = (
            "You are a route optimizer. "
            "Output ONLY valid JSON, no text."
        )
        user_prompt = self._construct_prompt(
            locations_data,
            constraints,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        loop = asyncio.get_event_loop()

        output = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: llm.create_chat_completion(
                    messages=messages,
                    temperature=0.1,
                    max_tokens=1024,
                    repeat_penalty=1.2,
                ),
            ),
            timeout=self.timeout,
        )

        content = output["choices"][0]["message"]["content"]

        if not content.endswith("}") and "{" in content:
            content += "}"

        return content

    def _construct_prompt(
        self,
        locations: List[Dict],
        constraints: Dict | None,
    ) -> str:
        # Используем nearest-neighbors вместо всех пар:
        # 50 точек × 3 соседа = 150 строк вместо 1225 (O(n²) → O(n·k))
        region = detect_region_info(locations)
        dm = compute_distance_matrix(locations)
        nn = build_nearest_neighbors(dm, k=3)

        locations_text = format_locations_compact(locations)
        nn_text = format_nearest_neighbors(locations, nn)
        constraints_text = build_constraints_text(constraints)

        fuel_rate = (constraints or {}).get("fuel_rate", 7.0)
        speed = 25 if region["classification"] == "urban" else 40
        n = len(locations)

        # Предвычисляем первый и последний ID для примера
        first_id = locations[0]["ID"] if locations else "id_first"
        last_id = locations[-1]["ID"] if locations else "id_last"

        return (
            f"Optimize delivery route: {n} stops, "
            f"{region['classification']} area ({region['area_km2']} km2).\n\n"
            f"STOPS (ID|name|lat,lon|priority):\n{locations_text}\n\n"
            f"NEAREST 3 NEIGHBORS per stop:\n{nn_text}\n\n"
            f"RULES: {constraints_text} "
            f"Speed={speed}km/h + 15min/stop. "
            f"Cost=dist*{fuel_rate}rub/km. "
            f"Priority A>B>C>D. Visit ALL stops once.\n\n"
            f"Return ONLY valid JSON, no markdown, no explanation:\n"
            f'{{"locations_sequence":["{first_id}",...,"{last_id}"],'
            f'"total_distance_km":0.0,'
            f'"total_time_hours":0.0,'
            f'"total_cost_rub":0.0}}'
        )

    def _parse_response(
        self,
        text_content: str,
        original_locations: List[Location],
    ) -> Route:
        try:
            logger.info("content: %s", text_content)
            text_content = text_content.strip()

            if text_content.startswith("```json"):
                text_content = text_content[7:]
            if text_content.endswith("```"):
                text_content = text_content[:-3]

            json_start = text_content.find("{")
            json_end = text_content.rfind("}") + 1

            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON brackets found")

            clean_json = text_content[json_start:json_end]
            data = json.loads(clean_json)

            new_route_id = str(uuid.uuid4())

            return Route(
                ID=new_route_id,
                name="Optimized Route (Llama GGUF)",
                locations=original_locations,
                total_distance_km=float(
                    data.get("total_distance_km", 0),
                ),
                total_time_hours=float(
                    data.get("total_time_hours", 0),
                ),
                total_cost_rub=float(
                    data.get("total_cost_rub", 0),
                ),
                model_used="llama-gguf-local",
                created_at=datetime.now(),
            )

        except Exception as exc:
            logger.error(
                "JSON Parse Error. Raw text: %s",
                text_content,
            )
            raise LlamaServerError(
                f"Failed to parse model response: {exc}",
            ) from exc

    async def analyze_metrics(self, data: Dict) -> str:
        return "Not implemented"

    async def health_check(self) -> bool:
        return LlamaClient._llm is not None
