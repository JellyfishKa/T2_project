import asyncio
import json
import logging
from datetime import datetime
from time import time
from typing import Dict, List

try:
    from llama_cpp import Llama
except ImportError:
    raise ImportError("Please install llama-cpp-python: "
                      "pip install llama-cpp-python")

from src.config import settings
from src.models.exceptions import (
    TProServerError,
    TProTimeoutError,
    TProValidationError,
)
from src.models.llm_client import LLMClient
from src.models.schemas import Location, Route

logger = logging.getLogger("tpro_client")


class TProClient(LLMClient):
    _llm = None

    def __init__(self):
        self.model_name = settings.tpro_model_id
        self.timeout = 30
        try:
            self.model_path = settings.get_model_path(settings.tpro_model_id)
        except FileNotFoundError as e:
            logger.error(str(e))
            self.model_path = None

    def _get_generator(self):
        """Lazy Loading модели через llama.cpp"""
        if TProClient._llm is None:
            if not self.model_path:
                raise TProServerError(
                    f"Model file {self.model_name} not found in project directories.",
                )

            try:
                logger.info(f"Loading GGUF model from {self.model_path}...")
                TProClient._llm = Llama(
                    model_path=self.model_path,
                    n_threads=4,
                    n_threads_batch=4,
                    n_gpu_layers=0,
                    n_batch=512,
                    n_ctx=512,
                )
                logger.info("GGUF model loaded successfully.")
            except Exception as e:
                logger.error(f"Critical error loading GGUF model: {e}")
                raise TProServerError(f"Failed to load GGUF model: {e}")

        return TProClient._llm

    async def generate_route(self, locations: List[Location],
                             constraints: Dict = None) -> Route:
        if not locations:
            raise TProValidationError("Locations list is empty")

        start_time = time()
        max_retries = 3

        locations_data = [loc.model_dump() for loc in locations]

        for attempt in range(1, max_retries + 2):
            try:
                response_text = await self._run_inference(locations_data,
                                                          constraints)
                result = self._parse_response(response_text, locations)

                duration = time() - start_time
                if duration > 3.0:
                    logger.warning(f"T-Pro slow response: {duration:.2f}s")

                return result

            except Exception as e:
                if attempt <= max_retries:
                    logger.warning(f"Retry {attempt}/{max_retries} due to: {e}")
                else:
                    logger.error("All retries exhausted.")
                    raise TProServerError(f"Generation failed: {e}")

    async def _run_inference(self, locations_data: List[Dict],
                             constraints: Dict) -> str:
        """Запуск инференса в отдельном потоке,
        так как llama.cpp блокирующая"""
        llm = self._get_generator()

        system_prompt = (
            "You are a logistics expert. "
            "You MUST return ONLY valid JSON with "
            "no markdown formatting or explanations."
        )

        user_prompt = self._construct_prompt(locations_data, constraints)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        loop = asyncio.get_event_loop()

        try:
            output = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: llm.create_chat_completion(
                        messages=messages,
                        temperature=0.1,
                        max_tokens=1024,
                    ),
                ),
                timeout=self.timeout,
            )

            content = output["choices"][0]["message"]["content"]
            return content

        except asyncio.TimeoutError:
            raise TProTimeoutError(f"Generation timed out after {self.timeout}s")
        except Exception as e:
            raise TProServerError(f"Inference error: {e}")

    def _construct_prompt(
        self,
        locations: List[Dict],
        constraints: Dict,
    ) -> str:
        locations_json = json.dumps(locations, ensure_ascii=False)
        constraints_str = json.dumps(constraints) if constraints else "{}"

        return f"""
        Role: You are a professional logistics expert specializing
        in route optimization in Russia.
        Task:
        1. Optimize the route for the provided locations.
        2. Prioritize high-priority points.
        3. Estimate the total cost in RUB based on average petrol prices
        for the region identified in the addresses.

        Input Data:
        Locations: {locations_json}
        Constraints: {constraints_str}

        Output Format:
        Return ONLY a valid JSON object matching exactly this schema
        (no markdown, no comments):
        {{
            "route_id": "string",
            "locations_sequence": ["id_from_input", ...],
            "total_distance_km": float,
            "total_time_hours": float,
            "total_cost_rub": float,
            "model_used": "{self.model_name}",
            "created_at": "{datetime.now().isoformat()}"
        }}
        """

    def _parse_response(self, text_content: str,
                        original_locations: List[Location]) -> Route:
        try:

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

            return Route(
                ID=str(data.get("route_id", f"tpro-{int(time())}")),
                name="Optimized Route (GGUF)",
                locations=original_locations,
                total_distance_km=float(data.get("total_distance_km", 0)),
                total_time_hours=float(data.get("total_time_hours", 0)),
                total_cost_rub=float(data.get("total_cost_rub", 0)),
                model_used="tpro-gguf-local",
                created_at=datetime.now(),
            )
        except Exception as e:
            logger.error(f"JSON Parse Error. Raw text: {text_content}")
            raise TProServerError(f"Failed to parse model response: {e}")

    async def analyze_metrics(self, data: Dict) -> str:
        return "Not implemented"

    async def health_check(self) -> bool:
        return TProClient._llm is not None
