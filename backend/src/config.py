from pathlib import Path

from dotenv import load_dotenv

from pydantic import ConfigDict

from pydantic_settings import BaseSettings

load_dotenv()
BASE_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    hf_token: str | None = None

    qwen_api_endpoint: str
    qwen_model_id: str

    tpro_api_endpoint: str
    tpro_model_id: str

    llama_api_endpoint: str
    llama_model_id: str

    database_user: str
    database_password: str
    database_host: str
    database_port: int = 5432
    database_name: str

    model_config = ConfigDict(env_file=BASE_DIR / ".env")

    def get_model_path(self, model_id: str) -> str:
        """
        Универсальный поиск GGUF файла модели.
        1. Проверяет абсолютный путь.
        2. Ищет в папке src/models.
        3. Ищет в корне backend.
        """
        if not model_id:
            raise ValueError("model_id cannot be empty")

        model_file = Path(model_id)

        # 1. Проверка абсолютного или относительного пути от текущей папки
        if model_file.exists():
            return str(model_file)

        # 2. Поиск в директории src/models
        models_dir = BASE_DIR / "src" / "models"
        path_in_models = models_dir / model_id
        if path_in_models.exists():
            return str(path_in_models)

        # 3. Поиск в корне проекта
        root_path = BASE_DIR / model_id
        if root_path.exists():
            return str(root_path)

        raise FileNotFoundError(
            f"GGUF model file not found: {model_id}",
        )


settings = Settings()
