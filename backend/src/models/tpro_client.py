from .llm_client import LLMClient

class TProClient(LLMClient):
    """
    Клиент для взаимодействия с T-Pro API.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def generate(self, prompt: str) -> str:
        # TODO: Реализовать API вызов
        if not prompt:
            raise ValueError("Промпт не может быть пустым")
        return f"T-Pro ответ на промпт: {prompt}"
