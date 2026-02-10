from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List


class LLMStatus(Enum):
    """
    Статусы выполнения запроса к LLM.

    Execution statuses for LLM requests.
    """

    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"


class Location:
    """
    DTO-заглушка для локации маршрута.

    Stub DTO for route location.
    """

    pass


class LLMClient(ABC):
    """
    Абстрактный базовый класс для всех LLM клиентов.

    Abstract base class for all LLM clients (GigaChat, Cotype, T-Pro).
    Используется как контракт и фундамент для fallback-механизма.
    """

    @abstractmethod
    async def generate_route(self, locations: List[Location]) -> str:
        """
        Генерация оптимального маршрута на основе списка локаций.

        Generate an optimal route based on a list of locations.

        :param locations: Список точек маршрута / List of route locations
        :return: Описание маршрута в текстовом виде / Route description as text
        """
        raise NotImplementedError

    @abstractmethod
    async def analyze_metrics(self, data: Dict) -> str:
        """
        Анализ метрик и возврат текстового отчёта.

        Analyze metrics data and return a textual report.

        :param data: Произвольные метрики / Arbitrary metrics data
        :return: Результат анализа / Analysis result
        """
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Проверка доступности и работоспособности LLM.

        Check availability and health of the LLM.

        :return: True если модель доступна / True if model is healthy
        """
        raise NotImplementedError
