from dataclasses import dataclass

from obsidian2anki.cli.handlers import NoteId, CardId


@dataclass(frozen=True)
class BaseCommandDefinition:
    name: str
    help: str
    func_name: str


@dataclass(frozen=True)
class CommandDefinition(BaseCommandDefinition):
    supports_dry_run: bool = True
    supports_recursive: bool = False


@dataclass(frozen=True)
class ArgCommandDefinition(BaseCommandDefinition):
    arg_name: str
    arg_help: str
    handler: NoteId | CardId


DOCTOR_COMMAND: CommandDefinition = CommandDefinition(
    name="doctor",
    help="Check application health.",
    supports_dry_run=False,
    func_name="run",
)

COMMANDS: tuple[CommandDefinition, ...] = (
    CommandDefinition(
        name="migrate",
        help="Run the full migration over the main notes folder.",
        func_name="migrate",
        supports_recursive=True,
    ),
    CommandDefinition(
        name="process",
        help="Process new notes from the inbox folder.",
        func_name="process",
        supports_recursive=True,
    ),
    CommandDefinition(
        name="clear",
        help="Delete all generated cards and clear state.",
        func_name="clear",
    ),
    CommandDefinition(
        name="format-notes",
        help="Convert existing notes to the required application format.",
        func_name="format_notes",
        supports_recursive=True,
    ),
    CommandDefinition(
        name="stats",
        help="Check application stats.",
        func_name="stats",
        supports_dry_run=False,
        supports_recursive=True,
    ),
)

ARG_COMMANDS: tuple[ArgCommandDefinition, ...] = (
    ArgCommandDefinition(
        name="delete-card",
        help="Delete a single Anki card by ID.",
        arg_name="card_id",
        arg_help="ID of the Anki card to delete.",
        handler=CardId,
        func_name="delete_card",
    ),
    ArgCommandDefinition(
        name="delete-note",
        help="Delete a single vault note by ID.",
        arg_name="note_id",
        arg_help="ID of the note to delete.",
        handler=NoteId,
        func_name="delete_note",
    ),
)

APP_COMMANDS = (*COMMANDS, *ARG_COMMANDS)
