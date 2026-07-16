import logging

from obsidian2anki.core.note_processor import NoteProcessor
from obsidian2anki.core.state_manager import StateManager
from obsidian2anki.core.vault_manager import VaultManager
from obsidian2anki.config import Settings, get_settings
from obsidian2anki.models import VaultNote


logger = logging.getLogger(__name__)
settings: Settings = get_settings()


class ProcessingService:
    def __init__(
        self, vault: VaultManager, state: StateManager, note_processor: NoteProcessor
    ) -> None:
        self._vault = vault
        self._state = state
        self._note_processor = note_processor

    def process(self) -> None:
        try:
            self._process()
        finally:
            self._state.save()

    def _process(self) -> None:
        notes: list[VaultNote] = self._vault.get_folder_notes(settings.INBOX_FOLDER)
        if not notes:
            logger.info("No notes found in '%s'.", settings.INBOX_FOLDER)
            return

        logger.info(
            "Found %d notes in '%s'.",
            len(notes),
            settings.INBOX_FOLDER,
        )

        for note in notes:
            self._note_processor.process_note(note)
