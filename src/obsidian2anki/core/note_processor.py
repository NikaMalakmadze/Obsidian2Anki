from pathlib import Path
import logging

from obsidian2anki.models import Flashcard, NoteInfo, VaultNote
from obsidian2anki.core.vault_manager import VaultManager
from obsidian2anki.core.state_manager import StateManager
from obsidian2anki.core.anki_manager import AnkiManager
from obsidian2anki.config import Settings, get_settings
from obsidian2anki.core.ai import AI

logger = logging.getLogger(__name__)
settings: Settings = get_settings()


class NoteProcessor:
    """Handles the lifecycle of a single note: cards, metadata, and state."""

    def __init__(
        self,
        ai: AI,
        anki: AnkiManager,
        state: StateManager,
        vault: VaultManager,
    ) -> None:
        self._ai = ai
        self._anki = anki
        self._state = state
        self._vault = vault

    def needs_processing(self, note: VaultNote) -> bool:
        """Whether a note is new or has changed since it was last processed."""
        return not self._state.in_state(note.id) or self._state.has_changed(
            note.id, note.title, note.content
        )

    def has_right_tags(self, note: VaultNote) -> bool:
        """Whether a note has right tags to be processed"""
        return all(tag not in note.tags for tag in settings.EXLUDE_TAGS) and any(
            tag in note.tags for tag in settings.INCLUDE_TAGS
        )

    def process_note(self, note: VaultNote) -> bool:
        """Generate flashcards for a single note. Returns success/failure."""
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

            ids: list[int] | None = self._anki.add_cards(note.id, flash_cards)

            tries: int = 0

            while not ids and tries < settings.MAX_RETRIES_ON_ANKI_DUBLICATE_CARD:
                tries += 1

                logger.warning(
                    "Failed to add cards for note '%s'. Retrying (%d/%d).",
                    note.id,
                    tries,
                    settings.MAX_RETRIES_ON_ANKI_DUBLICATE_CARD,
                )

                flash_cards: list[Flashcard] = self._ai.generate_note_cards(note)

                logger.info(
                    "Regenerated %d flash cards for note '%s'.",
                    len(flash_cards),
                    note.id,
                )

                ids: list[int] | None = self._anki.add_cards(note.id, flash_cards)

            if not ids:
                logger.error(
                    "Failed to add cards for note '%s' after %d attempts.",
                    note.id,
                    settings.MAX_RETRIES_ON_ANKI_DUBLICATE_CARD,
                )
                return False

            self._vault.write_metadata(note, ids)
            self._state.prepare_for_state(NoteInfo(vault_info=note, card_ids=ids))

            logger.info("Processed note with id: '%s'.", note.id)
            return True
        except Exception:
            logger.exception("Failed processing note with id '%s'.", note.id)
            return False

    def delete_note_cards(self, note_id: str, card_ids: list[int]) -> None:
        """Deletes all flash cards of note with given id"""
        self._state.delete_note_cards(note_id)
        note_path: Path = Path(self._state.get_property_of(note_id, "path"))
        self._vault.remove_property(note_path)
        for card_id in card_ids:
            self._anki.delete_card(card_id)
