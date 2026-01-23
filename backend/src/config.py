from pathlib import Path

from dotenv import load_dotenv

from pydantic import ConfigDict

from pydantic_settings import BaseSettings

load_dotenv()
BASE_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    hf_token: str | None = None
    gigachat_model_id: str
    cotype_model_id: str
    tpro_model_id: str

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
