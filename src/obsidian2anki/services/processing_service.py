import logging

from obsidian2anki.core.note_processor import NoteProcessor
from obsidian2anki.core.state_manager import StateManager
from obsidian2anki.core.vault_manager import VaultManager
from obsidian2anki.models import VaultNote


logger = logging.getLogger(__name__)


class ProcessingService:
    def __init__(
        self, vault: VaultManager, state: StateManager, note_processor: NoteProcessor
    ) -> None:
        self._vault = vault
        self._state = state
        self._note_processor = note_processor

    def process(self, dry_run: bool = False) -> None:
        try:
            self._process(dry_run)
        finally:
            self._state.save()

    def _process(self, dry_run: bool = False) -> None:
        notes: list[VaultNote] = self._vault.get_folder_notes(
            self._vault.settings.INBOX_FOLDER
        )
        if not notes:
            logger.info("No notes found in '%s'.", self._vault.settings.INBOX_FOLDER)
            return

        logger.info(
            "Found %d notes in '%s'.",
            len(notes),
            self._vault.settings.INBOX_FOLDER,
        )

        if dry_run:
            logger.debug("Ended processing on dry run.")
            return

        for note in notes:
            if self._note_processor.has_right_tags(note):
                self._note_processor.process_note(note)
