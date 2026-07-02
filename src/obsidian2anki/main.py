import sys

from obsidian2anki.core.vault_manager import VaultManager
from obsidian2anki.core.state_manager import StateManager
from obsidian2anki.core.anki_manager import AnkiManager
from obsidian2anki.config import get_settings, Settings
from obsidian2anki.models import Flashcard, NoteInfo
from obsidian2anki.core.ai import AI


settings: Settings = get_settings()


class Obsidian2Anki:
    def __init__(self) -> None:
        self._state: StateManager = StateManager()
        self._vault: VaultManager = VaultManager()
        self._anki: AnkiManager = AnkiManager()
        self._ai: AI = AI()

    def process(self) -> None:
        notes = self._vault._process_files(settings.INBOX_FOLDER)

        if not notes:
            print("No Notes Found")

        for note in notes:
            if self._state.in_state(note.title, note.content):
                continue

            flash_cards: list[Flashcard] = self._ai.generate_note_cards(note)
            ids: list[int] = self._anki.add_cards(flash_cards)
            self._vault.write_metadata(note, ids)
            self._state.update_state(NoteInfo(vault_info=note, card_ids=ids))

        if self._state.is_changed():
            self._state.set_state()

    def delete_card(self, card_id: str):
        try:
            card_id: int = int(card_id)
        except (ValueError, TypeError):
            print("Invalid Id")

        self._anki.delete_card(card_id)


if __name__ == "__main__":
    o2a: Obsidian2Anki = Obsidian2Anki()
    if len(sys.argv) == 2:
        o2a.delete_card(sys.argv[1])
        print("Deleted")
    else:
        o2a.process()
        print("Processed")
