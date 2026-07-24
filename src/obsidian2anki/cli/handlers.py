from collections.abc import Callable
from typing import TypeAlias

NoteId: TypeAlias = str
CardId: TypeAlias = int

ArgTypes: TypeAlias = NoteId | CardId

CommandHandler: TypeAlias = Callable[[], None]
ArgCommandHandler: TypeAlias = Callable[[NoteId | CardId], None]
