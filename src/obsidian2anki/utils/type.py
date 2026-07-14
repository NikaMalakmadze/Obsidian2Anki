from pydantic import BaseModel, Field
from typing import Literal, TypedDict


Action = Literal["deckNames", "changeDeck", "addNotes", "deleteNotes", "getTags"]

StateNoteProperties = Literal[
    "title",
    "path",
    "content_hash",
    "card_count",
    "anki_note_ids",
    "processed_at",
    "updated_at",
]


class DeckParamsDict(TypedDict, total=False):
    cards: list[str] = []
    deck: str = ""


class DeckParams(BaseModel):
    cards: list[str] = Field(default_factory=list)
    deck: str = ""
