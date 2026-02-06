from pathlib import Path

from dotenv import load_dotenv

from pydantic import ConfigDict

from pydantic_settings import BaseSettings

load_dotenv()
BASE_DIR = Path(__file__).parent.parent  # Это корень проекта (backend)


class Settings(BaseSettings):
    hf_token: str | None = None

    qwen_api_endpoint: str
    qwen_model_id: str

    tpro_api_endpoint: str
    tpro_model_id: str

    model_config = ConfigDict(env_file=BASE_DIR / ".env")

    def get_tpro_model_path(self) -> str:
        """
        Пытается найти файл модели.
        1. Сначала проверяет абсолютный путь.
        2. Затем ищет в папке src/models (рядом с клиентом).
        3. Затем ищет в корне backend.
        """
        if Path(self.tpro_model_id).exists():
            return self.tpro_model_id

        models_dir = BASE_DIR / "src" / "models"
        model_path = models_dir / self.tpro_model_id
        if model_path.exists():
            return str(model_path)

        root_path = BASE_DIR / self.tpro_model_id
        if root_path.exists():
            return str(root_path)

        raise FileNotFoundError(f"GGUF model not found: {self.tpro_model_id}")


settings = Settings()
