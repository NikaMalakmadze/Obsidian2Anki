import logging


logger = logging.getLogger(__name__)


class Obsidian2Anki:
    """High-level interface for managing the Obsidian-to-Anki workflow.

    This class coordinates the application's core operations, including
    migrating existing notes, processing new or updated notes into Anki
    flashcards, clearing generated data, and deleting individual cards.
    """

    def __init__(self, migration, processing, clear, card_deleting) -> None:
        """Initialize the application and its dependencies."""
        self._migration = migration
        self._processing = processing
        self._clear = clear
        self._card_deleting = card_deleting

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
        self._clear.clear()
        logger.info("Finished clearing everything.")

    def delete_card(self, card_id: str) -> None:
        """Delete an Anki card by its identifier.

        Args:
            card_id: The unique identifier of the Anki card to delete.
        """
        logger.info("Starting deleting card with id: `%s`.", card_id)
        self._card_deleting.delete_card(card_id)
        logger.info("Ended deleting card with id`%s`.", card_id)
