"""
Unit-тесты для QwenClient (Неделя 3).

Проверяют контракт, обработку ошибок и fallback-механизм.
Используют mock для избежания реальных вызовов модели.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio


class MockLocation:
    """Mock для Location."""
    def __init__(self, id, name, lat, lon, priority="B"):
        self.ID = id
        self.name = name
        self.lat = lat
        self.lon = lon
        self.priority = priority

    def model_dump(self):
        return {
            "ID": self.ID,
            "name": self.name,
            "lat": self.lat,
            "lon": self.lon,
            "priority": self.priority,
        }


@pytest.fixture
def sample_locations():
    """Минимальный набор локаций для тестов."""
    return [
        MockLocation("loc-1", "Store A", 55.75, 37.62, "A"),
        MockLocation("loc-2", "Store B", 55.76, 37.63, "B"),
        MockLocation("loc-3", "Store C", 55.74, 37.61, "C"),
    ]


@pytest.fixture
def mock_llm_response():
    """Mock ответа от LLM."""
    return {
        "route_id": "route-001",
        "locations_sequence": ["loc-1", "loc-3", "loc-2"],
        "total_distance_km": 12.5,
        "total_time_hours": 0.5,
        "total_cost_rub": 250.0,
        "model_used": "qwen",
        "created_at": "2026-02-16T12:00:00",
    }


class TestQwenClientInit:
    """Тесты инициализации QwenClient."""

    def test_client_instantiation(self):
        """Клиент может быть создан."""
        with patch("src.models.qwen_client.settings") as mock_settings:
            mock_settings.qwen_model_id = "qwen2-0_5b-instruct-q4_k_m.gguf"
            mock_settings.get_model_path.return_value = "/path/to/model.gguf"

            from src.models.qwen_client import QwenClient
            client = QwenClient()

            assert client.model_name == "qwen2-0_5b-instruct-q4_k_m.gguf"
            assert client.timeout == 120

    def test_client_without_model_file(self):
        """Клиент создаётся даже без файла модели."""
        with patch("src.models.qwen_client.settings") as mock_settings:
            mock_settings.qwen_model_id = "nonexistent.gguf"
            mock_settings.get_model_path.side_effect = FileNotFoundError("Not found")

            from src.models.qwen_client import QwenClient
            client = QwenClient()

            assert client.model_path is None


class TestQwenClientGenerateRoute:
    """Тесты generate_route метода."""

    @pytest.mark.asyncio
    async def test_generate_route_success(self, sample_locations, mock_llm_response):
        """Успешная генерация маршрута."""
        import json

        with patch("src.models.qwen_client.settings") as mock_settings, \
             patch("src.models.qwen_client.Llama") as mock_llm_class:

            mock_settings.qwen_model_id = "qwen.gguf"
            mock_settings.get_model_path.return_value = "/path/to/qwen.gguf"

            mock_llm_instance = MagicMock()
            mock_llm_instance.create_chat_completion.return_value = {
                "choices": [{
                    "message": {
                        "content": json.dumps(mock_llm_response)
                    }
                }]
            }
            mock_llm_class.return_value = mock_llm_instance

            from src.models.qwen_client import QwenClient
            client = QwenClient()

            result = await client.generate_route(sample_locations)

            assert result is not None
            assert result.total_distance_km == 12.5
            assert result.model_used == "qwen"

    @pytest.mark.asyncio
    async def test_generate_route_empty_locations(self):
        """Ошибка при пустом списке локаций."""
        with patch("src.models.qwen_client.settings") as mock_settings:
            mock_settings.qwen_model_id = "qwen.gguf"
            mock_settings.get_model_path.return_value = "/path/to/qwen.gguf"

            from src.models.qwen_client import QwenClient
            from src.models.exceptions import QwenValidationError

            client = QwenClient()

            with pytest.raises(QwenValidationError):
                await client.generate_route([])


class TestQwenClientHealthCheck:
    """Тесты health_check метода."""

    @pytest.mark.asyncio
    async def test_health_check_not_loaded(self):
        """Health check возвращает False если модель не загружена."""
        with patch("src.models.qwen_client.settings") as mock_settings:
            mock_settings.qwen_model_id = "qwen.gguf"
            mock_settings.get_model_path.return_value = "/path/to/qwen.gguf"

            from src.models.qwen_client import QwenClient

            QwenClient._llm = None
            client = QwenClient()

            result = await client.health_check()
            assert result is False

    @pytest.mark.asyncio
    async def test_health_check_loaded(self):
        """Health check возвращает True если модель загружена."""
        with patch("src.models.qwen_client.settings") as mock_settings, \
             patch("src.models.qwen_client.Llama") as mock_llm_class:

            mock_settings.qwen_model_id = "qwen.gguf"
            mock_settings.get_model_path.return_value = "/path/to/qwen.gguf"
            mock_llm_class.return_value = MagicMock()

            from src.models.qwen_client import QwenClient

            client = QwenClient()
            QwenClient._llm = MagicMock()

            result = await client.health_check()
            assert result is True


class TestQwenClientPromptConstruction:
    """Тесты конструирования промптов."""

    def test_construct_prompt_includes_locations(self, sample_locations):
        """Промпт включает информацию о локациях в компактном формате."""
        with patch("src.models.qwen_client.settings") as mock_settings:
            mock_settings.qwen_model_id = "qwen.gguf"
            mock_settings.get_model_path.return_value = "/path/to/qwen.gguf"

            from src.models.qwen_client import QwenClient
            client = QwenClient()

            locations_data = [loc.model_dump() for loc in sample_locations]
            prompt = client._construct_prompt(locations_data, None)

            assert "Store A" in prompt
            assert "Store B" in prompt
            assert "55.75" in prompt
            assert "STOPS" in prompt
            assert "nearest" in prompt.lower()

    def test_construct_prompt_includes_constraints(self, sample_locations):
        """Промпт включает ограничения."""
        with patch("src.models.qwen_client.settings") as mock_settings:
            mock_settings.qwen_model_id = "qwen.gguf"
            mock_settings.get_model_path.return_value = "/path/to/qwen.gguf"

            from src.models.qwen_client import QwenClient
            client = QwenClient()

            locations_data = [loc.model_dump() for loc in sample_locations]
            constraints = {"team_size": 4, "fuel_rate": 8.0}
            prompt = client._construct_prompt(locations_data, constraints)

            assert "Team: 4" in prompt
            assert "8.0" in prompt

    def test_construct_prompt_has_json_example(self, sample_locations):
        """Промпт включает JSON few-shot пример."""
        with patch("src.models.qwen_client.settings") as mock_settings:
            mock_settings.qwen_model_id = "qwen.gguf"
            mock_settings.get_model_path.return_value = "/path/to/qwen.gguf"

            from src.models.qwen_client import QwenClient
            client = QwenClient()

            locations_data = [loc.model_dump() for loc in sample_locations]
            prompt = client._construct_prompt(locations_data, None)

            assert "locations_sequence" in prompt
            assert "total_distance_km" in prompt
            assert "0.0" in prompt


class TestQwenClientResponseParsing:
    """Тесты парсинга ответов."""

    def test_parse_valid_json_response(self, sample_locations, mock_llm_response):
        """Корректный парсинг валидного JSON ответа."""
        import json

        with patch("src.models.qwen_client.settings") as mock_settings:
            mock_settings.qwen_model_id = "qwen.gguf"
            mock_settings.get_model_path.return_value = "/path/to/qwen.gguf"

            from src.models.qwen_client import QwenClient
            client = QwenClient()

            response_text = json.dumps(mock_llm_response)
            result = client._parse_response(response_text, sample_locations)

            assert result.total_distance_km == 12.5
            assert result.total_time_hours == 0.5
            assert result.total_cost_rub == 250.0

    def test_parse_markdown_wrapped_response(self, sample_locations, mock_llm_response):
        """Парсинг ответа, обёрнутого в markdown."""
        import json

        with patch("src.models.qwen_client.settings") as mock_settings:
            mock_settings.qwen_model_id = "qwen.gguf"
            mock_settings.get_model_path.return_value = "/path/to/qwen.gguf"

            from src.models.qwen_client import QwenClient
            client = QwenClient()

            response_text = f"```json\n{json.dumps(mock_llm_response)}\n```"
            result = client._parse_response(response_text, sample_locations)

            assert result.total_distance_km == 12.5

    def test_parse_invalid_json_raises_error(self, sample_locations):
        """Ошибка при невалидном JSON."""
        with patch("src.models.qwen_client.settings") as mock_settings:
            mock_settings.qwen_model_id = "qwen.gguf"
            mock_settings.get_model_path.return_value = "/path/to/qwen.gguf"

            from src.models.qwen_client import QwenClient
            from src.models.exceptions import QwenServerError

            client = QwenClient()

            with pytest.raises(QwenServerError):
                client._parse_response("This is not JSON", sample_locations)


class TestQwenClientFallback:
    """Тесты fallback-механизма (Qwen -> Llama)."""

    @pytest.mark.asyncio
    async def test_fallback_on_model_not_found(self, sample_locations):
        """Fallback когда файл модели не найден."""
        with patch("src.models.qwen_client.settings") as mock_settings:
            mock_settings.qwen_model_id = "nonexistent.gguf"
            mock_settings.get_model_path.side_effect = FileNotFoundError("Not found")

            from src.models.qwen_client import QwenClient
            from src.models.exceptions import QwenServerError

            QwenClient._llm = None
            client = QwenClient()

            with pytest.raises(QwenServerError):
                await client.generate_route(sample_locations)