from obsidian2anki.vault_manager import VaultManager
from obsidian2anki.anki_manager import AnkiManager
from obsidian2anki.ai import AI

v = VaultManager()
ai = AI()
am = AnkiManager()

notes = v.process_files()

print(notes)

names: list[str] = [note.title for note in notes]

cards = []
for note in notes:
    cards.extend(ai.generate_note_cards(note))

print(cards)

ids = am.add_cards(cards)

print(ids)
