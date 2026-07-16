from pathlib import Path
import logging

from obsidian2anki.core.note_processor import NoteProcessor
from obsidian2anki.core.state_manager import StateManager
from obsidian2anki.core.vault_manager import VaultManager
from obsidian2anki.config import Settings, get_settings

logger = logging.getLogger(__name__)
settings: Settings = get_settings()


class ClearService:
    def __init__(
        self, vault: VaultManager, state: StateManager, note_processor: NoteProcessor
    ) -> None:
        self._vault = vault
        self._state = state
        self._note_processor = note_processor

    def clear(self) -> None:
        state_items = self._state.get_state_items()

        logger.info("Founded %d notes in state", len(state_items))

        for id, info in state_items:
            self._note_processor.delete_note_cards(id, info.anki_note_ids)
            self._vault.remove_property(Path(info.path))

            logger.info("Deleted note with id: '%s'", id)

        self._state.clear_state()
