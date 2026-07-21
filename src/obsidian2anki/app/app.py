from typing import Protocol
import logging


logger = logging.getLogger(__name__)


class NoteFormatterService(Protocol):
    def format_notes(self) -> None: ...


class MigrationService(Protocol):
    def migrate(self) -> None: ...


class ProcessingService(Protocol):
    def process(self) -> None: ...


class ClearService(Protocol):
    def clear(self) -> None: ...


class DeletingService(Protocol):
    def delete_card(self, card_id: str) -> None: ...
    def delete_note(self, note_id: str) -> None: ...


class Obsidian2Anki:
    """High-level interface for managing the Obsidian-to-Anki workflow.

    This class coordinates the application's core operations, including
    migrating existing notes, processing new or updated notes into Anki
    flashcards, clearing generated data, and deleting individual cards.
    """

    def __init__(
        self,
        migration: MigrationService,
        processing: ProcessingService,
        clearing: ClearService,
        deleting: DeletingService,
        note_formatter: NoteFormatterService,
    ) -> None:
        self._migration = migration
        self._processing = processing
        self._clearing = clearing
        self._deleting = deleting
        self._note_formatter = note_formatter

    def migrate(self) -> None:
        """Initialize tracking and synchronize existing notes.

        Performs the initial setup by registering notes in the application's
        state and processing any existing notes whose content differs from the
        recorded state.
        """
        logger.info("Starting migration.")
        self._migration.migrate()
        logger.info("Migration completed.")

    def process(self) -> None:
        """Process notes and synchronize them with Anki.

        Detects new notes, generates flashcards when needed, updates the
        application state, and synchronizes changes with Anki.
        """
        logger.info("Starting processing notes.")
        self._processing.process()
        logger.info("Finished processing notes.")

    def clear(self) -> None:
        """Remove all application-managed data.

        Clears tracked state and any generated resources managed by the
        application.
        """
        logger.info("Started clearing everything.")
        self._clearing.clear()
        logger.info("Finished clearing everything.")

    def delete_card(self, card_id: str) -> None:
        """Delete an Anki card by its identifier.

        Args:
            card_id: The unique identifier of the Anki card to delete.
        """
        logger.info("Starting deleting card with id: `%s`.", card_id)
        self._deleting.delete_card(card_id)
        logger.info("Ended deleting card with id`%s`.", card_id)

    def delete_note(self, note_id: str) -> None:
        """Delete a vault note by its identifier from state and deleting its all cards.

        Args:
            note_id: The unique identifier of the vault note to delete.
        """
        logger.info("Starting deleting note with id: `%s`.", note_id)
        self._deleting.delete_note(note_id)
        logger.info("Ended deleting card note id`%s`.", note_id)

    def format_notes(self) -> None:
        """Convert existing notes to the required Obsidian2Anki format."""
        logger.info("Starting note formatting.")
        self._note_formatter.format_notes()
        logger.info("Note formatting completed.")
