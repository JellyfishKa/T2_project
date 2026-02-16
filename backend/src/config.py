<<<<<<< Updated upstream
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

    model_config = ConfigDict(env_file=BASE_DIR / ".env")


settings = Settings()


# ------- Проверка корректности работы модели - id получен ------- #
# from transformers import AutoTokenizer

# AutoTokenizer.from_pretrained(
#     settings.gigachat_model_id,
#     token=settings.hf_token,
# )

# AutoTokenizer.from_pretrained(
#     settings.cotype_model_id,
#     token=settings.hf_token,
# )

# AutoTokenizer.from_pretrained(
#     settings.tpro_model_id,
#     token=settings.hf_token,
# )
=======
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    hf_token: str | None = None

    qwen_api_endpoint: str = "local"
    qwen_model_id: str = "qwen2-0_5b-instruct-q4_k_m.gguf"

    llama_api_endpoint: str = "local"
    llama_model_id: str = "Llama-3.2-1B-Instruct-Q4_K_M.gguf"

    database_user: str = "postgres"
    database_password: str = "postgres"
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "t2"

    debug: bool = False

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

        if model_file.exists():
            return str(model_file)

        models_dir = BASE_DIR / "src" / "models"
        path_in_models = models_dir / model_id
        if path_in_models.exists():
            return str(path_in_models)

        root_path = BASE_DIR / model_id
        if root_path.exists():
            return str(root_path)

        raise FileNotFoundError(
            f"GGUF model file not found: {model_id}",
        )


settings = Settings()
>>>>>>> Stashed changes
