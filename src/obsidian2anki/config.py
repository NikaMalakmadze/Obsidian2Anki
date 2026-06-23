from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path

BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config: SettingsConfigDict = SettingsConfigDict(env_file=BASE_DIR / ".env")

    ANKI_URL: str


@lru_cache
def get_settings() -> Settings:
    return Settings()
