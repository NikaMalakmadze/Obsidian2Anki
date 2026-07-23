from dataclasses import dataclass
from obsidian2anki.cli.handlers import NoteId, CardId


@dataclass(frozen=True)
class CommandDefinition:
    name: str
    help: str
    supports_dry_run: bool = True


@dataclass(frozen=True)
class ArgCommandDefinition:
    name: str
    help: str
    arg_name: str
    arg_help: str
    handler: NoteId | CardId


COMMANDS: tuple[CommandDefinition, ...] = (
    CommandDefinition(
        name="migrate",
        help="Run the full migration over the main notes folder.",
    ),
    CommandDefinition(
        name="process",
        help="Process new notes from the inbox folder.",
    ),
    CommandDefinition(
        name="clear",
        help="Delete all generated cards and clear state.",
    ),
    CommandDefinition(
        name="format-notes",
        help="Convert existing notes to the required application format.",
    ),
    CommandDefinition(
        name="doctor",
        help="Check application health.",
        supports_dry_run=False,
    ),
)

ARG_COMMANDS: tuple[ArgCommandDefinition, ...] = (
    ArgCommandDefinition(
        name="delete-card",
        help="Delete a single Anki card by ID.",
        arg_name="card_id",
        arg_help="ID of the Anki card to delete.",
        handler=CardId,
    ),
    ArgCommandDefinition(
        name="delete-note",
        help="Delete a single vault note by ID.",
        arg_name="note_id",
        arg_help="ID of the note to delete.",
        handler=NoteId,
    ),
)
