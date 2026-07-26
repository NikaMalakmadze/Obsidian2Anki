from google.genai.errors import APIError, ClientError
from pathlib import Path
from google import genai
import logging
import time

from obsidian2anki.models import FlashcardBatch, VaultNote, Flashcard
from obsidian2anki.config import get_settings, Settings, BASE_DIR


logger = logging.getLogger(__name__)
settings: Settings = get_settings()


class AI:
    def __init__(self, delay: int = 7) -> None:
        self.delay: int = delay
        self.prompt: str = self._get_prompt()
        self.client = genai.Client(api_key=settings.API_KEY)

    def generate_note_cards(self, note: VaultNote) -> list[Flashcard]:
        while True:
            try:
                response = self.client.models.generate_content(
                    model="gemini-3.1-flash-lite",
                    contents=self.prompt
                    + f"\n\n{note.model_dump_json(indent=2, exclude=['id', 'path', 'anki_cards'])}",
                    config={
                        "response_mime_type": "application/json",
                        "response_schema": FlashcardBatch,
                    },
                )
                break
            except ClientError:
                logger.warning("Rate limit hit. Retrying in %s seconds...", self.delay)
                time.sleep(self.delay)
                self.delay = min(self.delay * 2, 60)

        cards: FlashcardBatch = FlashcardBatch.model_validate_json(response.text)
        return cards.cards

    @staticmethod
    def validate_key(api_key: str) -> bool:
        try:
            client = genai.Client(api_key=api_key)
            client.models.list()
            logger.debug("API key is valid")
            return True
        except APIError:
            logger.error("Authentication failed - invalid API key: '%s'", api_key)
            return False
        except Exception:
            logger.exception("An unexpected error occurred")
            return False

    @staticmethod
    def _get_prompt() -> str:
        prompt_file: Path = BASE_DIR / settings.PROMPT_FILE
        return prompt_file.read_text(encoding="utf-8")
