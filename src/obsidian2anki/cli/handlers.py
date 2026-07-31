from typing import NewType
from collections.abc import Callable

NoteId = NewType("NoteId", str)
CardId = NewType("CardId", int)

type ArgTypes = NoteId | CardId

type CommandHandler = Callable[[], None]
type ArgCommandHandler = Callable[[ArgTypes], None]
