import logging
from pathlib import Path

from obsidian2anki.core.vault_manager import VaultManager
from obsidian2anki.core.state_manager import StateManager
from obsidian2anki.core.anki_manager import AnkiManager
from obsidian2anki.config import Settings, get_settings

logger = logging.getLogger(__name__)
settings: Settings = get_settings()


class DeleteCardService:
    def __init__(
        self, vault: VaultManager, state: StateManager, anki: AnkiManager
    ) -> None:
        self._anki = anki
        self._state = state
        self._vault = vault

    def delete_card(self, card_id: str) -> None:
        try:
            card_id: int = int(card_id)
        except (ValueError, TypeError):
            logger.error("Invalid card id: %s", card_id)
            return

        note_id: str = self._state.delete_card(card_id)
        if not note_id:
            logger.warning("Card with id: %d not found in state.", card_id)
            return

        note_path: Path = Path(self._state.get_property_of(note_id, "path"))

        self._anki.delete_card(card_id)
        self._vault.remove_list_item(note_path, "anki_cards", str(card_id))
