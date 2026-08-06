import logging
from typing import Any

from obsidian2anki.exceptions import AnkiResponseError
from obsidian2anki.utils.anki_connecter import AnkiConnecter
from obsidian2anki.models import Flashcard, AnkiCard

logger = logging.getLogger(__name__)


class AnkiManager(AnkiConnecter):
    def __init__(self) -> None:
        super().__init__()
        self.deck_name: str = self.settings.DECK_NAME

    def get_decks(self) -> list[str]:
        return self.connect("deckNames")

    def get_tags(self) -> list[str]:
        return self.connect("getTags")

    def get_notes(self) -> list[int]:
        return self.connect("findNotes", query=f"deck:{self.deck_name}")

    def delete_card(self, id: int) -> None:
        self.connect("deleteNotes", notes=[id])

    def create_deck(self, name: str = "") -> None:
        deck_name: str = name if name else self.deck_name
        v = self.connect("createDeck", deck=deck_name)
        if v:
            logger.info("Deck with name: '%s' created.", deck_name)

    def add_cards(
        self, note_id: str, cards: list[Flashcard], deck_name: str = ""
    ) -> list[int] | None:
        self.create_deck_if_not(deck_name)

        anki_cards: list[AnkiCard] = [
            self._create_anki_note(note_id, card, deck_name) for card in cards
        ]

        result: Any = self.connect(
            "addNotes", notes=[card.serialize() for card in anki_cards]
        )

        if not isinstance(result, list):
            raise AnkiResponseError("addNotes result must be a list of note IDs.")

        if len(result) != len(cards):
            raise AnkiResponseError(
                f"Expected {len(cards)} note IDs, received {len(result)}."
            )

        if any(not isinstance(anki_id, int) for anki_id in result):
            raise AnkiResponseError("addNotes returned an invalid note ID.")

        return result

    def create_deck_if_not(self, deck_name: str) -> None:
        user_decks: list[str] = self.get_decks()

        if self.deck_name not in user_decks or (
            deck_name and deck_name not in user_decks
        ):
            self.create_deck(deck_name if deck_name else self.deck_name)

    def _create_anki_note(self, note_id: str, card: Flashcard, deck_name: str = ""):
        return AnkiCard(
            deck_name=deck_name if deck_name else self.deck_name,
            front=card.question,
            back=card.answer,
            tags=card.tags,
            note_id=note_id,
        )
