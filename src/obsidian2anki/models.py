from pydantic import BaseModel, Field

from obsidian2anki.utils.type import NoneEmptyText


class VaultNote(BaseModel):
    id: str
    title: str
    tags: list[str]
    content: str
    path: str
    anki_cards: list[int]


class Flashcard(BaseModel):
    question: NoneEmptyText
    answer: NoneEmptyText
    tags: list[str]


class FlashcardBatch(BaseModel):
    cards: list[Flashcard] = Field(min_length=1, max_length=5)


class AnkiCard(BaseModel):
    deck_name: str
    model_name: str = "Basic"
    front: str
    back: str
    note_id: str
    tags: list[str] = Field(default_factory=list)

    def serialize(self) -> dict:
        return {
            "deckName": self.deck_name,
            "modelName": self.model_name,
            "fields": {
                "Front": self.front,
                "Back": self.back,
                "NoteID": self.note_id,
            },
            "tags": self.tags,
        }


class StateNote(BaseModel):
    title: str
    path: str
    content_hash: str
    card_count: int
    anki_note_ids: list[int]
    processed_at: str
    updated_at: str


class NoteInfo(BaseModel):
    vault_info: VaultNote
    card_ids: list[int]
