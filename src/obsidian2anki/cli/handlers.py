from collections.abc import Callable
from typing import TypeAlias

CommandHandler: TypeAlias = Callable[[], None]
NoteId: TypeAlias = str
CardId: TypeAlias = int
