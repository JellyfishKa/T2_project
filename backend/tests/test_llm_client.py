import pytest

from src.models.cotype_client import CotypeClient
from src.models.gigachat_client import GigaChatClient
from src.models.llm_client import LLMClient, LLMStatus, Location
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


class DummyLLMClient(LLMClient):
    """
    Тестовая реализация LLMClient для проверки абстрактного контракта.
    """

    async def generate_route(self, locations: list[Location]) -> str:
        return "ok"

    async def analyze_metrics(self, data: dict) -> str:
        return "ok"

    async def health_check(self) -> bool:
        return True


def test_llm_client_can_be_instantiated_via_child():
    """
    Проверяем, что конкретная реализация LLMClient может быть создана.
    """
    client = DummyLLMClient()
    assert isinstance(client, LLMClient)


def test_llm_status_enum_values():
    """
    Проверяем Enum статусов.
    """
    assert LLMStatus.SUCCESS.value == "success"
    assert LLMStatus.FAILURE.value == "failure"
    assert LLMStatus.TIMEOUT.value == "timeout"


@pytest.mark.asyncio
async def test_generate_route_contract():
    """
    Проверка контракта generate_route.
    """
    client = DummyLLMClient()
    result = await client.generate_route([])
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_analyze_metrics_contract():
    """
    Проверка контракта analyze_metrics.
    """
    client = DummyLLMClient()
    result = await client.analyze_metrics({})
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_health_check_contract():
    """
    Проверка контракта health_check.
    """
    client = DummyLLMClient()
    result = await client.health_check()
    assert isinstance(result, bool)
