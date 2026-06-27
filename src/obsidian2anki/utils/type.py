from typing import Literal, TypedDict

Action = Literal["deckNames", "changeDeck", "addNotes", "deleteNotes", "getTags"]


class DeckParamsDict(TypedDict, total=False):
    cards: list[str] = []
    deck: str = ""
