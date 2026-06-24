from google import genai

from obsidian2anki.models import FlashcardBatch, VaultNote, Flashcard
from obsidian2anki.config import get_settings, Settings

settings: Settings = get_settings()


class AI:
    def __init__(self) -> None:
        self.client = genai.Client(api_key=settings.API_KEY)
        self.prompt: str = """
You are an expert teacher and flashcard creator.

Your task is to generate high-quality Anki flashcards from the provided note.

Rules:
1. Create cards only for important concepts.
2. Do NOT create cards for obvious facts.
3. Prefer conceptual understanding over rote memorization.
4. For programming notes:
   - Focus on definitions.
   - Focus on concepts.
   - Focus on common interview questions.
   - Focus on common mistakes.
5. Do not generate duplicate cards.
6. Keep answers concise.
7. Generate between 1 and 5 cards depending on note complexity.
8. Preserve the language of the note. If the note is Georgian, cards should be Georgian.

Note:
"""

    def generate_note_cards(self, note: VaultNote) -> list[Flashcard]:
        response = self.client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=self.prompt + f"\n\n{note.model_dump_json(indent=2)}",
            config={
                "response_mime_type": "application/json",
                "response_schema": FlashcardBatch,
            },
        )

        cards: FlashcardBatch = FlashcardBatch.model_validate_json(response.text)
        return cards.cards
