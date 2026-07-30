from collections.abc import Callable

type NoteId = str
type CardId = int

type ArgTypes = NoteId | CardId

type CommandHandler = Callable[[], None]
type ArgCommandHandler = Callable[[NoteId | CardId], None]
