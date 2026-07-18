from pathlib import Path
import logging

from obsidian2anki.core.note_processor import NoteProcessor
from obsidian2anki.core.state_manager import StateManager
from obsidian2anki.core.vault_manager import VaultManager
from obsidian2anki.config import Settings, get_settings


logger = logging.getLogger(__name__)
settings: Settings = get_settings()


class NoteFormatterService:
    def __init__(
        self, vault: VaultManager, state: StateManager, note_processor: NoteProcessor
    ) -> None:
        self._vault = vault
        self._state = state
        self._note_processor = note_processor

    def ensure_notes_format(self) -> None:
        main_notes_folder_path: Path = (
            Path(settings.LOCAL_VAULT) / settings.MAIN_NOTES_FOLDER
        )

        for file in main_notes_folder_path.iterdir():
            if file.is_file():
                self._vault.ensure_note_format(file)
                logger.info("Formatting file with path: '%s'.", str(file.resolve()))
