from obsidian2anki.services.notes_formatter import NoteFormatterService
from obsidian2anki.services.processing_service import ProcessingService
from obsidian2anki.services.migration_service import MigrationService
from obsidian2anki.services.deleting_service import DeletingService
from obsidian2anki.services.clear_service import ClearService

from obsidian2anki.core.note_processor import NoteProcessor
from obsidian2anki.core.vault_manager import VaultManager
from obsidian2anki.core.state_manager import StateManager
from obsidian2anki.core.anki_manager import AnkiManager
from obsidian2anki.core.ai import AI

from obsidian2anki.app.doctor import Doctor


class Dependencies:
    """
    Central dependency container.

    Creates every shared object exactly once and wires them together.
    Services receive the dependencies they need through constructor
    injection rather than creating them internally.
    """

    def __init__(self) -> None:
        self.vault = VaultManager()
        self.anki = AnkiManager()
        self.state = StateManager()
        self.ai = AI()
        self.note_processor = NoteProcessor(self.ai, self.anki, self.state, self.vault)

        self._migration = MigrationService(self.vault, self.state, self.note_processor)
        self._processing = ProcessingService(
            self.vault, self.state, self.note_processor
        )
        self._clear = ClearService(self.vault, self.state, self.note_processor)
        self._deleting = DeletingService(self.vault, self.state, self.anki)
        self._note_formatting = NoteFormatterService(self.vault)

        self._doctor = Doctor(self.ai, self.anki)
