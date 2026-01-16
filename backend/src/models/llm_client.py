from abc import ABC, abstractmethod

class LLMClient(ABC):
    """
    Абстрактный базовый класс для LLM клиентов.
    """
    
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """
        Генерирует текст на основе предоставленного промпта.
        
        Args:
            prompt: Входной текстовый промпт.
            
        Returns:
            Генерируемый текстовый ответ.
        """
        pass
