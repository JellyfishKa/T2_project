"""
Unit-тесты для API routes (qwen, llama).

Проверяют корректность работы endpoints и обработку ошибок.
Используют моки для избежания зависимости от sqlalchemy.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime
import json


class MockLocation:
    """Mock для Location."""
    def __init__(self, id, name, lat, lon):
        self.ID = id
        self.name = name
        self.lat = lat
        self.lon = lon

    def model_dump(self):
        return {
            "ID": self.ID,
            "name": self.name,
            "lat": self.lat,
            "lon": self.lon,
        }


class MockRoute:
    """Mock для Route."""
    def __init__(self, **kwargs):
        self.ID = kwargs.get("ID", "route-001")
        self.name = kwargs.get("name", "Test Route")
        self.locations = kwargs.get("locations", [])
        self.total_distance_km = kwargs.get("total_distance_km", 10.0)
        self.total_time_hours = kwargs.get("total_time_hours", 0.5)
        self.total_cost_rub = kwargs.get("total_cost_rub", 100.0)
        self.model_used = kwargs.get("model_used", "qwen")
        self.created_at = kwargs.get("created_at", datetime.now())

    def model_dump(self):
        return {
            "ID": self.ID,
            "name": self.name,
            "locations": [loc.model_dump() if hasattr(loc, 'model_dump') else loc for loc in self.locations],
            "total_distance_km": self.total_distance_km,
            "total_time_hours": self.total_time_hours,
            "total_cost_rub": self.total_cost_rub,
            "model_used": self.model_used,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
        }


@pytest.fixture
def sample_locations():
    """Минимальный набор локаций для тестов."""
    return [
        MockLocation("loc-1", "Store A", 55.75, 37.62),
        MockLocation("loc-2", "Store B", 55.76, 37.63),
    ]


class TestQwenClientRoute:
    """Тесты для QwenClient через routes."""

    @pytest.mark.asyncio
    async def test_generate_route_success(self, sample_locations):
        """Успешная генерация маршрута через Qwen."""
        with patch("src.models.qwen_client.settings") as mock_settings, \
             patch("src.models.qwen_client.Llama") as mock_llm_class:

            mock_settings.qwen_model_id = "qwen.gguf"
            mock_settings.get_model_path.return_value = "/path/to/qwen.gguf"

            mock_llm_instance = MagicMock()
            mock_llm_instance.create_chat_completion.return_value = {
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "route_id": "route-001",
                            "locations_sequence": ["loc-1", "loc-2"],
                            "total_distance_km": 12.5,
                            "total_time_hours": 0.5,
                            "total_cost_rub": 250.0,
                            "model_used": "qwen",
                            "created_at": "2026-02-16T12:00:00",
                        })
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


class TestLlamaClientRoute:
    """Тесты для LlamaClient через routes."""

    @pytest.mark.asyncio
    async def test_generate_route_success(self, sample_locations):
        """Успешная генерация маршрута через Llama."""
        with patch("src.models.llama_client.settings") as mock_settings, \
             patch("src.models.llama_client.Llama") as mock_llm_class:

            mock_settings.llama_model_id = "llama.gguf"
            mock_settings.get_model_path.return_value = "/path/to/llama.gguf"

            mock_llm_instance = MagicMock()
            mock_llm_instance.create_chat_completion.return_value = {
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "route_id": "route-llama-001",
                            "locations_sequence": ["loc-2", "loc-1"],
                            "total_distance_km": 10.5,
                            "total_time_hours": 0.4,
                            "total_cost_rub": 200.0,
                            "model_used": "llama",
                            "created_at": "2026-02-16T12:00:00",
                        })
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


class TestRouteErrorHandling:
    """Тесты обработки ошибок в routes."""

    def test_qwen_validation_error_content(self):
        """Тест контента ошибки QwenValidationError."""
        from src.models.exceptions import QwenValidationError

        error = QwenValidationError("Test error message")
        assert "Test error message" in str(error)

    def test_llama_validation_error_content(self):
        """Тест контента ошибки LlamaValidationError."""
        from src.models.exceptions import LlamaValidationError

        error = LlamaValidationError("Invalid locations")
        assert "Invalid locations" in str(error)

    def test_qwen_server_error_content(self):
        """Тест контента ошибки QwenServerError."""
        from src.models.exceptions import QwenServerError

        error = QwenServerError("Model not loaded")
        assert "Model not loaded" in str(error)

    def test_llama_server_error_content(self):
        """Тест контента ошибки LlamaServerError."""
        from src.models.exceptions import LlamaServerError

        error = LlamaServerError("Inference failed")
        assert "Inference failed" in str(error)


class TestFallbackMechanism:
    """Тесты fallback-механизма Qwen -> Llama -> Greedy."""

    @pytest.mark.asyncio
    async def test_fallback_sequence(self, sample_locations):
        """Тест последовательности fallback."""
        with patch("src.models.qwen_client.settings") as mock_qwen_settings, \
             patch("src.models.llama_client.settings") as mock_llama_settings:

            mock_qwen_settings.qwen_model_id = "qwen.gguf"
            mock_qwen_settings.get_model_path.side_effect = FileNotFoundError("Qwen not found")

            mock_llama_settings.llama_model_id = "llama.gguf"
            mock_llama_settings.get_model_path.return_value = "/path/to/llama.gguf"

            with patch("src.models.llama_client.Llama") as mock_llm_class:
                mock_llm_instance = MagicMock()
                mock_llm_instance.create_chat_completion.return_value = {
                    "choices": [{
                        "message": {
                            "content": json.dumps({
                                "route_id": "fallback-route",
                                "locations_sequence": ["loc-1", "loc-2"],
                                "total_distance_km": 10.0,
                                "total_time_hours": 0.4,
                                "total_cost_rub": 200.0,
                                "model_used": "llama",
                                "created_at": "2026-02-16T12:00:00",
                            })
                        }
                    }]
                }
                mock_llm_class.return_value = mock_llm_instance

                from src.models.qwen_client import QwenClient
                from src.models.llama_client import LlamaClient

                QwenClient._llm = None
                qwen_client = QwenClient()

                with pytest.raises(Exception):
                    await qwen_client.generate_route(sample_locations)

                LlamaClient._llm = None
                llama_client = LlamaClient()
                result = await llama_client.generate_route(sample_locations)

                assert result is not None
                assert "llama" in result.model_used.lower()