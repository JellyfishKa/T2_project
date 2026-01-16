from .llm_client import LLMClient

class GigaChatClient(LLMClient):
    """
    Клиент для взаимодействия с GigaChat API.
    """
    
    def __init__(self, token: str, api_url: str):
        self.token = token
        self.api_url = api_url
        
    def generate(self, prompt: str) -> str:
        # TODO: Реализовать API вызов
        if not prompt:
            raise ValueError("Промпт не может быть пустым")
        return f"GigaChat ответ на промпт: {prompt}"