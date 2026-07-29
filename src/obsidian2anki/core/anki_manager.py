import logging

from obsidian2anki.utils.anki_connecter import AnkiConnecter
from obsidian2anki.config import Settings, get_settings
from obsidian2anki.models import Flashcard, AnkiCard

logger = logging.getLogger(__name__)
settings: Settings = get_settings()


class AnkiManager(AnkiConnecter):
    def __init__(self) -> None:
        super().__init__()
        self.deck_name: str = settings.DECK_NAME

    def get_decks(self) -> list[str]:
        return self.connect("deckNames")

    def get_tags(self) -> list[str]:
        return self.connect("getTags")

    def get_notes(self) -> list[int]:
        return self.connect("findNotes", query=f"deck:{self.deck_name}")

    def create_deck(self, name: str = "") -> None:
        deck_name: str = name if name else self.deck_name
        v = self.connect("createDeck", deck=deck_name)
        if v:
            logger.info("Deck with name: '%s' created.", deck_name)

    def add_cards(
        self, note_id: str, cards: list[Flashcard], deck_name: str = ""
    ) -> list[int] | None:
        user_decks: list[str] = self.get_decks()

        if self.deck_name not in user_decks or (
            deck_name and deck_name not in user_decks
        ):
            self.create_deck(deck_name if deck_name else self.deck_name)

        anki_cards: list[AnkiCard] = [
            AnkiCard(
                deck_name=deck_name if deck_name else self.deck_name,
                front=card.question,
                back=card.answer,
                tags=card.tags,
                note_id=note_id,
            )
            for card in cards
        ]

        ids: list[int] | None = self.connect(
            "addNotes", notes=[card.serialize() for card in anki_cards]
        )

        return ids

    def delete_card(self, id: int) -> None:
        self.connect("deleteNotes", notes=[id])
