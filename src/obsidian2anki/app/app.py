from typing import Protocol
import logging


logger = logging.getLogger(__name__)


class DoctorService(Protocol):
    """Interface for running application diagnostic checks."""

    def run(self) -> None:
        """Run all application health checks."""
        ...


class StatsService(Protocol):
    """Interface for getting stats about program"""

    def stats(self, recursive: bool = False) -> None:
        """Get application stats"""
        ...


class NoteFormatterService(Protocol):
    """Interface for formatting vault legacy notes."""

    def ensure_notes_format(
        self, dry_run: bool = False, recursive: bool = False
    ) -> None:
        """Format notes into the structure required by the application."""
        ...


class MigrationService(Protocol):
    """Interface for performing the full note migration."""

    def migrate(self, dry_run: bool = False, recursive: bool = False) -> None:
        """Migrate and synchronize existing vault notes."""
        ...


class ProcessingService(Protocol):
    """Interface for processing new notes."""

    def process(self, dry_run: bool = False, recursive: bool = False) -> None:
        """Process notes and synchronize generated cards with Anki."""
        ...


class ClearService(Protocol):
    """Interface for clearing application-managed data."""

    def clear(self, dry_run: bool = False) -> None:
        """Clear generated cards and application state."""
        ...


class DeletingService(Protocol):
    """Interface for deleting cards and notes."""

    def delete_card(self, card_id: int, dry_run: bool = False) -> None:
        """Delete an Anki card by its identifier."""
        ...

    def delete_note(self, note_id: str, dry_run: bool = False) -> None:
        """Delete a note and its associated Anki cards."""
        ...


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
        stats: StatsService,
    ) -> None:
        self._migration = migration
        self._processing = processing
        self._clearing = clearing
        self._deleting = deleting
        self._note_formatter = note_formatter
        self._stats = stats

    def migrate(self, dry_run: bool = False, recursive: bool = False) -> None:
        """Initialize tracking and synchronize existing notes.

        Performs the initial setup by registering notes in the application's
        state and processing any existing notes whose content differs from the
        recorded state.

        Args:
            dry_run: If ``True``, report the planned changes without modifying the vault, application state, or Anki.
        """
        logger.info("Starting migration.")
        self._migration.migrate(dry_run, recursive)
        logger.info("Migration completed.")

    def process(self, dry_run: bool = False, recursive: bool = False) -> None:
        """Process notes and synchronize them with Anki.

        Detects new notes, generates flashcards when needed, updates the
        application state, and synchronizes changes with Anki.

        Args:
            dry_run: If ``True``, report the planned changes without modifying the vault, application state, or Anki.
        """
        logger.info("Starting processing notes.")
        self._processing.process(dry_run, recursive)
        logger.info("Finished processing notes.")

    def clear(self, dry_run: bool = False) -> None:
        """Remove all application-managed data.

        Clears tracked state and any generated resources managed by the
        application.

        Args:
            dry_run: If ``True``, report the planned changes without modifying the vault, application state, or Anki.
        """
        logger.info("Started clearing everything.")
        self._clearing.clear(dry_run)
        logger.info("Finished clearing everything.")

    def format_notes(self, dry_run: bool = False, recursive: bool = False) -> None:
        """Convert existing notes to the required Obsidian2Anki format.

        Args:
            dry_run: If ``True``, report the planned changes without modifying the vault, application state, or Anki.
        """
        logger.info("Starting note formatting.")
        self._note_formatter.ensure_notes_format(dry_run, recursive)
        logger.info("Note formatting completed.")

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

    def stats(self, recursive: bool = False) -> None:
        """Display statistics about the current application state.

        Collects and presents summary information about the managed notes,
        generated Anki cards, and other relevant application metrics.
        """
        logger.info("Generating application statistics.")
        self._stats.stats(recursive)
        logger.info("Application statistics generated.")
