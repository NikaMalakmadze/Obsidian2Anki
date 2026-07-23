from pathlib import Path
import logging

from obsidian2anki.core.vault_manager import VaultManager
from obsidian2anki.core.state_manager import StateManager
from obsidian2anki.core.anki_manager import AnkiManager

logger = logging.getLogger(__name__)


class DeletingService:
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
        ids_list: list[str] | None = self._vault.remove_list_item(
            note_path, "anki_cards", str(card_id)
        )
        if not ids_list:
            self._state.delete_state_item(note_id)

    def delete_note(self, note_id: str) -> None:
        if not self._state.in_state(note_id):
            logger.info("Note with id: '%s' is not in state", note_id)

        note_path: Path = Path(self._state.get_property_of(note_id, "path"))
        note_cards: list[int] = self._state.get_property_of(note_id, "anki_note_ids")

        for note_card in note_cards:
            self._anki.delete_card(note_card)

        self._vault.remove_property(note_path)

        self._state.delete_state_item(note_id)
