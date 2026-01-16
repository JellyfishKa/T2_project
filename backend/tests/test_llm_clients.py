import pytest
from unittest.mock import Mock, patch
from src.models.gigachat_client import GigaChatClient
from src.models.cotype_client import CotypeClient
from src.models.tpro_client import TProClient

class TestGigaChatClient:
    def test_generate_success(self):
        """TC-001: GigaChatClient возвращает текст из валидного ответа."""
        client = GigaChatClient(token="fake_token", api_url="http://fake.url")
        response = client.generate("test prompt")
        assert "GigaChat ответ" in response

    def test_empty_prompt_error(self):
        """TC-012: Пустой промпт вызывает ValueError."""
        client = GigaChatClient(token="fake_token", api_url="http://fake.url")
        with pytest.raises(ValueError):
            client.generate("")

class TestCotypeClient:
    def test_generate_success(self):
        """TC-002: CotypeClient возвращает текст из валидного ответа."""
        client = CotypeClient(model_path="/path/to/model")
        response = client.generate("test prompt")
        assert "Cotype ответ" in response

class TestTProClient:
    def test_generate_success(self):
        """TC-003: TProClient возвращает текст из валидного ответа."""
        client = TProClient(api_key="fake_key")
        response = client.generate("test prompt")
        assert "T-Pro ответ" in response

# Note: More comprehensive tests with mocks for HTTP failures will be added 
# once the actual HTTP logic is implemented in the clients.
