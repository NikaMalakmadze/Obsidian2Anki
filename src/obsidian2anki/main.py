from pathlib import Path
import logging
import sys

from obsidian2anki.models import Flashcard, NoteInfo, VaultNote
from obsidian2anki.core.vault_manager import VaultManager
from obsidian2anki.core.state_manager import StateManager
from obsidian2anki.core.anki_manager import AnkiManager
from obsidian2anki.config import get_settings, Settings
from obsidian2anki.utils.logger import setup_logger
from obsidian2anki.core.ai import AI


settings: Settings = get_settings()
logger = logging.getLogger(__name__)


class Obsidian2Anki:
    def __init__(self) -> None:
        self._state: StateManager = StateManager()
        self._vault: VaultManager = VaultManager()
        self._anki: AnkiManager = AnkiManager()
        self._ai: AI = AI()

    def migrate(self) -> None:
        logger.info("Starting migration.")

        main_folder_notes: list[VaultNote] = self._vault.get_folder_notes(
            settings.MAIN_NOTES_FOLDER
        )

        logger.info(
            "Found %d notes in '%s'.",
            len(main_folder_notes),
            settings.MAIN_NOTES_FOLDER,
        )

        for note in main_folder_notes:
            should_continue: bool = any(
                tag in note.tags for tag in settings.EXLUDE_TAGS
            ) or not any(tag in note.tags for tag in settings.INCLUDE_TAGS)

            should_process: bool = not self._state.in_state(
                note.id
            ) or self._state.has_changed(note.id, note.title, note.content)

            if should_continue:
                continue

            if should_process:
                self._process_note(note)

        self._state.set_state()

        logger.info("Migration completed.")

    def process(self) -> None:
        logger.info("Starting processing notes.")

        notes: list[VaultNote] = self._vault.get_folder_notes(settings.INBOX_FOLDER)

        logger.info(
            "Found %d notes in '%s'.",
            len(notes),
            settings.INBOX_FOLDER,
        )

        if not notes:
            logger.info("No notes found in '%s'.", settings.INBOX_FOLDER)
            return

        for note in notes:
            self._process_note(note)

        self._state.set_state()

        logger.info("Finished processing notes.")

    def clear(self) -> None:
        logger.info("Started clearing everything")

        state = self._state.state

        logger.info("Founded %d notes in state", len(state))

        for id, info in state.items():
            self.delete_note_cards(id, info.anki_note_ids)
            self._vault.remove_property(Path(info.path))

            logger.info("Deleted note with id: '%s'", id)

        self._state.clear_state()

        logger.info("Finished clearing everything")

    def delete_card(self, card_id: str) -> None:
        try:
            card_id: int = int(card_id)
        except (ValueError, TypeError):
            logger.error("Invalid card ID: %s", card_id)
            return

        if not self._state.delete_card(card_id):
            logger.warning("Card %d not found in state.", card_id)
            return

        self._anki.delete_card(card_id)

        logger.info("Deleted card %d.", card_id)

    def delete_note_cards(self, note_id: str, card_ids: list[int]) -> None:
        self._state.delete_note_cards(note_id)

        for card_id in card_ids:
            self._anki.delete_card(card_id)

    def _process_note(self, note: VaultNote) -> None:
        try:
            if note.anki_cards:
                self.delete_note_cards(note.id, note.anki_cards)
                logger.info(
                    "Deleted %d cards of note with id: '%s'.",
                    len(note.anki_cards),
                    note.id,
                )
            flash_cards: list[Flashcard] = self._ai.generate_note_cards(note)

            logger.info(
                "Generated %d flash cards for note with id: '%s'.",
                len(flash_cards),
                note.id,
            )

            ids: list[int] = self._anki.add_cards(flash_cards)
            self._vault.write_metadata(note, ids)
            self._state.prepare_for_state(NoteInfo(vault_info=note, card_ids=ids))

            logger.info("Processed note with id: '%s'.", note.id)

        except Exception:
            logger.exception("Failed processing note '%s'.", note.title)


if __name__ == "__main__":
    setup_logger()
    o2a: Obsidian2Anki = Obsidian2Anki()
    if len(sys.argv) == 2:
        o2a.delete_card(sys.argv[1])
        print("Deleted")
    else:
        o2a.process()
        print("Processed")
