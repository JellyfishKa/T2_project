from src.models.llm_client import LLMClient


class CotypeClient(LLMClient):
    """
    Клиент для взаимодействия с Cotype API.
    """

    def __init__(self, model_path: str):
        self.model_path = model_path

    def generate(self, prompt: str) -> str:
        # TODO: Реализовать локальный вызов модели или API
        if not prompt:
            raise ValueError("Промпт не может быть пустым")
        return f"Cotype ответ на промпт: {prompt}"
