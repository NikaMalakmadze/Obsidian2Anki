from pydantic import BaseModel, Field


class VaultNote(BaseModel):
    title: str
    tags: list[str]
    content: str
    path: str


class Flashcard(BaseModel):
    question: str
    answer: str
    tags: list[str]


class FlashcardBatch(BaseModel):
    cards: list[Flashcard]


class AnkiCard(BaseModel):
    deck_name: str
    model_name: str = "Basic"
    front: str
    back: str
    tags: list[str] = Field(default_factory=list)

    def serialize(self) -> dict:
        return {
            "deckName": self.deck_name,
            "modelName": self.model_name,
            "fields": {
                "Front": self.front,
                "Back": self.back,
            },
            "tags": self.tags,
        }


class DeckParams(BaseModel):
    cards: list[str] = Field(default_factory=list)
    deck: str = ""
