from collections.abc import Callable
from typing import NewType

NoteId = NewType("NoteId", str)
CardId = NewType("CardId", int)

type ArgTypes = NoteId | CardId

type CommandHandler = Callable[[], None]
type ArgCommandHandler = Callable[[ArgTypes], None]
