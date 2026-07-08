from pathlib import Path
from google import genai

from obsidian2anki.models import FlashcardBatch, VaultNote, Flashcard
from obsidian2anki.config import get_settings, Settings, BASE_DIR

settings: Settings = get_settings()


class AI:
    def __init__(self) -> None:
        self.client = genai.Client(api_key=settings.API_KEY)
        self.prompt: str = self._get_prompt()

    def generate_note_cards(self, note: VaultNote) -> list[Flashcard]:
        response = self.client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=self.prompt
            + f"\n\n{note.model_dump_json(indent=2, exclude=['id', 'path'])}",
            config={
                "response_mime_type": "application/json",
                "response_schema": FlashcardBatch,
            },
        )

        cards: FlashcardBatch = FlashcardBatch.model_validate_json(response.text)
        return cards.cards

    def _get_prompt(self) -> str:
        prompt_file: Path = BASE_DIR / settings.PROMPT_FILE
        return prompt_file.read_text(encoding="utf-8")
