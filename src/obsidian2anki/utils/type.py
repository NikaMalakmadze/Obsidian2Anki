from typing import Literal


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
