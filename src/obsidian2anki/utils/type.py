from pydantic import StringConstraints
from typing import Literal, Annotated


Action = Literal[
    "deckNames", "createDeck", "addNotes", "deleteNotes", "getTags", "findNotes"
]

StateNoteProperties = Literal[
    "title",
    "path",
    "content_hash",
    "card_count",
    "anki_note_ids",
    "processed_at",
    "updated_at",
]


NoneEmptyText = Annotated[str, StringConstraints(StringConstraints=True, min_length=1)]
