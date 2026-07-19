from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path

BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config: SettingsConfigDict = SettingsConfigDict(env_file=BASE_DIR / ".env")

    STATE_FOLDER: str

    API_KEY: str
    PROMPT_FILE: str

    INCLUDE_TAGS: list[str]
    EXCLUDE_TAGS: list[str]

    ANKI_URL: str
    DECK_NAME: str

    LOCAL_VAULT: str
    INBOX_FOLDER: str
    MAIN_NOTES_FOLDER: str

    MAX_RETRIES_ON_ANKI_DUPLICATE_CARD: int


@lru_cache
def get_settings() -> Settings:
    return Settings()
