"""
Unit-тесты для LlamaClient (Неделя 3).

Проверяют контракт, обработку ошибок и fallback-механизм.
Llama - fallback модель для Qwen.
"""

import pytest
from unittest.mock import MagicMock, patch
import json


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
        "route_id": "route-llama-001",
        "locations_sequence": ["loc-2", "loc-1", "loc-3"],
        "total_distance_km": 10.5,
        "total_time_hours": 0.4,
        "total_cost_rub": 200.0,
        "model_used": "llama-gguf-local",
        "created_at": "2026-02-16T12:00:00",
    }


class TestLlamaClientInit:
    """Тесты инициализации LlamaClient."""

    def test_client_instantiation(self):
        """Клиент может быть создан."""
        with patch("src.models.llama_client.settings") as mock_settings:
            mock_settings.llama_model_id = "Llama-3.2-1B-Instruct-Q4_K_M.gguf"
            mock_settings.get_model_path.return_value = "/path/to/llama.gguf"

            from src.models.llama_client import LlamaClient
            client = LlamaClient()

            assert client.model_name == "Llama-3.2-1B-Instruct-Q4_K_M.gguf"
            assert client.timeout == 120

    def test_client_without_model_file(self):
        """Клиент создаётся даже без файла модели."""
        with patch("src.models.llama_client.settings") as mock_settings:
            mock_settings.llama_model_id = "nonexistent.gguf"
            mock_settings.get_model_path.side_effect = FileNotFoundError("Not found")

            from src.models.llama_client import LlamaClient
            client = LlamaClient()

            assert client.model_path is None


class TestLlamaClientGenerateRoute:
    """Тесты generate_route метода."""

    @pytest.mark.asyncio
    async def test_generate_route_success(self, sample_locations, mock_llm_response):
        """Успешная генерация маршрута."""
        with patch("src.models.llama_client.settings") as mock_settings, \
             patch("src.models.llama_client.Llama") as mock_llm_class:

            mock_settings.llama_model_id = "llama.gguf"
            mock_settings.get_model_path.return_value = "/path/to/llama.gguf"

            mock_llm_instance = MagicMock()
            mock_llm_instance.create_chat_completion.return_value = {
                "choices": [{
                    "message": {
                        "content": json.dumps(mock_llm_response)
                    }
                }]
            }
            mock_llm_class.return_value = mock_llm_instance

            from src.models.llama_client import LlamaClient
            client = LlamaClient()

            result = await client.generate_route(sample_locations)

            assert result is not None
            assert result.total_distance_km == 10.5
            assert "llama" in result.model_used.lower()

    @pytest.mark.asyncio
    async def test_generate_route_empty_locations(self):
        """Ошибка при пустом списке локаций."""
        with patch("src.models.llama_client.settings") as mock_settings:
            mock_settings.llama_model_id = "llama.gguf"
            mock_settings.get_model_path.return_value = "/path/to/llama.gguf"

            from src.models.llama_client import LlamaClient
            from src.models.exceptions import LlamaValidationError

            client = LlamaClient()

            with pytest.raises(LlamaValidationError):
                await client.generate_route([])

    @pytest.mark.asyncio
    async def test_generate_route_retry_on_failure(self, sample_locations, mock_llm_response):
        """Повторные попытки при ошибках."""
        with patch("src.models.llama_client.settings") as mock_settings, \
             patch("src.models.llama_client.Llama") as mock_llm_class:

            mock_settings.llama_model_id = "llama.gguf"
            mock_settings.get_model_path.return_value = "/path/to/llama.gguf"

            mock_llm_instance = MagicMock()
            call_count = [0]

            def side_effect(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] < 3:
                    raise Exception("Temporary error")
                return {
                    "choices": [{
                        "message": {
                            "content": json.dumps(mock_llm_response)
                        }
                    }]
                }

            mock_llm_instance.create_chat_completion.side_effect = side_effect
            mock_llm_class.return_value = mock_llm_instance

            from src.models.llama_client import LlamaClient
            LlamaClient._llm = mock_llm_instance
            client = LlamaClient()

            result = await client.generate_route(sample_locations)

            assert result is not None
            assert call_count[0] == 3


class TestLlamaClientHealthCheck:
    """Тесты health_check метода."""

    @pytest.mark.asyncio
    async def test_health_check_not_loaded(self):
        """Health check возвращает False если модель не загружена."""
        with patch("src.models.llama_client.settings") as mock_settings:
            mock_settings.llama_model_id = "llama.gguf"
            mock_settings.get_model_path.return_value = "/path/to/llama.gguf"

            from src.models.llama_client import LlamaClient

            LlamaClient._llm = None
            client = LlamaClient()

            result = await client.health_check()
            assert result is False

    @pytest.mark.asyncio
    async def test_health_check_loaded(self):
        """Health check возвращает True если модель загружена."""
        with patch("src.models.llama_client.settings") as mock_settings, \
             patch("src.models.llama_client.Llama") as mock_llm_class:

            mock_settings.llama_model_id = "llama.gguf"
            mock_settings.get_model_path.return_value = "/path/to/llama.gguf"
            mock_llm_class.return_value = MagicMock()

            from src.models.llama_client import LlamaClient

            client = LlamaClient()
            LlamaClient._llm = MagicMock()

            result = await client.health_check()
            assert result is True


class TestLlamaClientResponseParsing:
    """Тесты парсинга ответов."""

    def test_parse_valid_json_response(self, sample_locations, mock_llm_response):
        """Корректный парсинг валидного JSON ответа."""
        with patch("src.models.llama_client.settings") as mock_settings:
            mock_settings.llama_model_id = "llama.gguf"
            mock_settings.get_model_path.return_value = "/path/to/llama.gguf"

            from src.models.llama_client import LlamaClient
            client = LlamaClient()

            response_text = json.dumps(mock_llm_response)
            result = client._parse_response(response_text, sample_locations)

            assert result.total_distance_km == 10.5
            assert result.total_time_hours == 0.4
            assert result.total_cost_rub == 200.0

    def test_parse_incomplete_json_auto_closes(self, sample_locations, mock_llm_response):
        """Автоматическое закрытие незавершённого JSON."""
        with patch("src.models.llama_client.settings") as mock_settings:
            mock_settings.llama_model_id = "llama.gguf"
            mock_settings.get_model_path.return_value = "/path/to/llama.gguf"

            from src.models.llama_client import LlamaClient
            client = LlamaClient()

            incomplete_json = json.dumps(mock_llm_response)[:-1]
            result = client._parse_response(incomplete_json + "}", sample_locations)

            assert result.total_distance_km == 10.5


class TestLlamaClientAsFallback:
    """Тесты Llama как fallback модели."""

    @pytest.mark.asyncio
    async def test_llama_used_when_qwen_fails(self, sample_locations, mock_llm_response):
        """Llama используется когда Qwen недоступен."""
        with patch("src.models.llama_client.settings") as mock_settings, \
             patch("src.models.llama_client.Llama") as mock_llm_class:

            mock_settings.llama_model_id = "llama.gguf"
            mock_settings.get_model_path.return_value = "/path/to/llama.gguf"

            mock_llm_instance = MagicMock()
            mock_llm_instance.create_chat_completion.return_value = {
                "choices": [{
                    "message": {
                        "content": json.dumps(mock_llm_response)
                    }
                }]
            }
            mock_llm_class.return_value = mock_llm_instance

            from src.models.llama_client import LlamaClient
            LlamaClient._llm = None
            client = LlamaClient()

            result = await client.generate_route(sample_locations)

            assert result is not None
            assert "llama" in result.model_used.lower()


class TestLlamaClientPromptConstruction:
    """Тесты конструирования промптов."""

    def test_construct_prompt_includes_locations(self, sample_locations):
        """Промпт включает информацию о локациях."""
        with patch("src.models.llama_client.settings") as mock_settings:
            mock_settings.llama_model_id = "llama.gguf"
            mock_settings.get_model_path.return_value = "/path/to/llama.gguf"

            from src.models.llama_client import LlamaClient
            client = LlamaClient()

            locations_data = [loc.model_dump() for loc in sample_locations]
            prompt = client._construct_prompt(locations_data, None)

            assert "Store A" in prompt
            assert "Store B" in prompt
            assert "STOPS" in prompt
            assert "NEAREST" in prompt

    def test_construct_prompt_includes_region_info(self, sample_locations):
        """Промпт включает информацию о регионе."""
        with patch("src.models.llama_client.settings") as mock_settings:
            mock_settings.llama_model_id = "llama.gguf"
            mock_settings.get_model_path.return_value = "/path/to/llama.gguf"

            from src.models.llama_client import LlamaClient
            client = LlamaClient()

            locations_data = [loc.model_dump() for loc in sample_locations]
            prompt = client._construct_prompt(locations_data, None)

            assert "rural" in prompt
            assert "km2" in prompt

    def test_construct_prompt_with_constraints(self, sample_locations):
        """Промпт включает ограничения."""
        with patch("src.models.llama_client.settings") as mock_settings:
            mock_settings.llama_model_id = "llama.gguf"
            mock_settings.get_model_path.return_value = "/path/to/llama.gguf"

            from src.models.llama_client import LlamaClient
            client = LlamaClient()

            locations_data = [loc.model_dump() for loc in sample_locations]
            constraints = {"team_size": 4, "fuel_rate": 8.0}
            prompt = client._construct_prompt(locations_data, constraints)

            assert "Team: 4" in prompt
            assert "8.0" in prompt
            assert "Visit ALL" in prompt