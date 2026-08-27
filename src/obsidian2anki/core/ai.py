from google.genai.errors import APIError, ClientError
from pydantic import ValidationError
from pathlib import Path
from google import genai
import logging
import random
import time


from obsidian2anki.exceptions import AIInvalidOutput, AIRequestFailed, AIRetryExhausted
from obsidian2anki.models import FlashcardBatch, VaultNote, Flashcard
from obsidian2anki.config import get_settings, Settings, BASE_DIR


logger = logging.getLogger(__name__)


class AI:
    def __init__(self) -> None:
        self.settings: Settings = get_settings()

        self.initial_delay: float = self.settings.AI_RETRY_BASE_DELAY
        self.max_delay: float = self.settings.AI_RETRY_MAX_DELAY
        self.max_retries: int = self.settings.AI_MAX_RETRIES

        self.client = genai.Client(api_key=self.settings.API_KEY)

    def generate_note_cards(self, note: VaultNote) -> list[Flashcard]:
        prompt: str = self._get_prompt()
        delay: float = self.initial_delay

        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.models.generate_content(
                    model="gemini-3.1-flash-lite",
                    contents=prompt
                    + f"\n\n{note.model_dump_json(indent=2, exclude=['id', 'path', 'anki_cards'])}",
                    config={
                        "response_mime_type": "application/json",
                        "response_schema": FlashcardBatch,
                    },
                )
                cards: FlashcardBatch = FlashcardBatch.model_validate_json(
                    response.text
                )

                logger.debug("Flashcard generation succeeded.")

                return cards.cards
            except ValidationError as exc:
                logger.error("Gemini returned invalid flashcards: %s", exc)
                raise AIInvalidOutput(
                    "Gemini returned invalid flashcard output."
                ) from exc
            except ClientError as exc:
                if attempt >= self.max_retries:
                    logger.error(
                        "Gemini request failed after %s retries.",
                        self.max_retries,
                    )
                    raise AIRequestFailed(
                        f"Gemini request failed after {self.max_retries} retries."
                    ) from exc

                delay = min(self.initial_delay * 2**attempt, self.max_delay)
                delay += random.uniform(0, 0.5)

                logger.warning("Rate limit hit. Retrying in %s seconds...", delay)

                time.sleep(delay)

        raise AIRetryExhausted(
            f"Failed to generate flashcards after {self.max_retries} attempts."
        )

    def _get_prompt(self) -> str:
        prompt_file: Path = BASE_DIR / self.settings.PROMPT_FILE
        return prompt_file.read_text(encoding="utf-8")

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
