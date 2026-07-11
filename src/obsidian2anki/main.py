import sys

from obsidian2anki.models import Flashcard, NoteInfo, VaultNote
from obsidian2anki.core.vault_manager import VaultManager
from obsidian2anki.core.state_manager import StateManager
from obsidian2anki.core.anki_manager import AnkiManager
from obsidian2anki.config import get_settings, Settings
from obsidian2anki.core.ai import AI


settings: Settings = get_settings()


class Obsidian2Anki:
    def __init__(self) -> None:
        self._state: StateManager = StateManager()
        self._vault: VaultManager = VaultManager()
        self._anki: AnkiManager = AnkiManager()
        self._ai: AI = AI()

    def migrate(self) -> None:
        main_folder_notes: list[VaultNote] = self._vault.get_folder_notes(
            settings.MAIN_NOTES_FOLDER
        )

        for note in main_folder_notes:
            if any(tag in note.tags for tag in settings.EXLUDE_TAGS):
                continue

            if not any(tag in note.tags for tag in settings.INCLUDE_TAGS):
                continue

            if not self._state.in_state(note.id) or self._state.has_changed(
                note.id, note.title, note.content
            ):
                self._process_note(note)

        self._state.set_state()

    def process(self) -> None:
        notes: list[VaultNote] = self._vault.get_folder_notes(settings.INBOX_FOLDER)

        if not notes:
            print("No Notes Found")
            return

        for note in notes:
            self._process_note(note)

        self._state.set_state()

    def delete_card(self, card_id: str) -> None:
        try:
            card_id: int = int(card_id)
        except (ValueError, TypeError):
            print("Invalid Id")
            return

        if not self._state.delete_card(card_id):
            print("Not Found")
            return

        self._anki.delete_card(card_id)

    def delete_note_cards(self, note_id: str, card_ids: list[int]) -> None:
        self._state.delete_note_cards(note_id)

        for card_id in card_ids:
            self._anki.delete_card(card_id)

    def _process_note(self, note: VaultNote) -> None:
        try:
            note.anki_cards and self.delete_note_cards(note.id, note.anki_cards)
            flash_cards: list[Flashcard] = self._ai.generate_note_cards(note)
            ids: list[int] = self._anki.add_cards(flash_cards)
            self._vault.write_metadata(note, ids)
            self._state.prepare_for_state(NoteInfo(vault_info=note, card_ids=ids))
        except Exception as e:
            print(f"Failed processing {note.title}: {e}")


if __name__ == "__main__":
    o2a: Obsidian2Anki = Obsidian2Anki()
    if len(sys.argv) == 2:
        o2a.delete_card(sys.argv[1])
        print("Deleted")
    else:
        o2a.process()
        print("Processed")
