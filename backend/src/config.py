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
    database_password: str = "change_me_in_env"
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "t2"

    debug: bool = False
    perf_warn_threshold_ms: int = 10_000
    routing_primary_mode: str = "algorithm_primary"
    routing_enable_llm_fallback: bool = True
    routing_llm_fallback_model: str = "llama"
    routing_quality_floor: float = 60.0
    routing_enable_llm_variant_evaluation: bool = False
    routing_allow_direct_llm_routes: bool = False
    routing_default_alternatives_count: int = 3
    routing_weight_distance: float = 0.4
    routing_weight_time: float = 0.3
    routing_weight_cost: float = 0.2
    routing_weight_quality: float = 0.1
    default_depot_lat: float = 54.1871
    default_depot_lon: float = 45.1749
    security_enable_api_key_auth: bool = False
    security_api_key: str | None = None
    security_admin_api_key: str | None = None
    security_allow_bulk_location_delete: bool = False
    security_allow_benchmark_run: bool = False

    @field_validator("debug", mode="before")
    @classmethod
    def _parse_debug(cls, value):
        if isinstance(value, bool) or value is None:
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug", "dev"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "prod", "production"}:
                return False
        return value

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
