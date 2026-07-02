from typing import Unpack

from obsidian2anki.utils.type import DeckParamsDict, DeckParams
from obsidian2anki.utils.anki_connecter import AnkiConnecter
from obsidian2anki.config import Settings, get_settings
from obsidian2anki.models import Flashcard, AnkiCard

settings: Settings = get_settings()


class AnkiManager(AnkiConnecter):
    def __init__(self) -> None:
        super().__init__()
        self.deck_name: str = settings.DECK_NAME

    def get_decks(self) -> list[str]:
        return self.connect("deckNames")

    def get_tags(self) -> list[str]:
        return self.connect("getTags")

    def create_deck(self, name: str = "", **params: Unpack[DeckParamsDict]) -> None:
        validated = self._validate_params(DeckParams, params)
        validated.deck = name if name else self.deck_name
        v = self.connect("changeDeck", **validated.model_dump())
        if not v:
            print("Created Deck")

    def add_cards(self, cards: list[Flashcard], deck_name: str = "") -> list[int]:
        if self.deck_name not in self.get_decks():
            self.create_deck(self.deck_name)

        if deck_name and deck_name not in self.get_decks():
            self.create_deck(self.deck_name)

        anki_cards: list[AnkiCard] = [
            AnkiCard(
                deck_name=deck_name if deck_name else self.deck_name,
                front=card.question,
                back=card.answer,
                tags=card.tags,
            )
            for card in cards
        ]

        ids: list[int] = self.connect(
            "addNotes", notes=[card.serialize() for card in anki_cards]
        )

        return ids

    def delete_card(self, id: int) -> None:
        self.connect("deleteNotes", notes=[id])
