from pathlib import Path
import logging

from obsidian2anki.exceptions import (
    AIInvalidOutput,
    AnkiDuplicateNoteError,
    AnkiError,
)
from obsidian2anki.models import Flashcard, NoteInfo, VaultNote
from obsidian2anki.core.vault_manager import VaultManager
from obsidian2anki.core.state_manager import StateManager
from obsidian2anki.core.anki_manager import AnkiManager
from obsidian2anki.config import Settings, get_settings
from obsidian2anki.core.ai import AI

logger = logging.getLogger(__name__)


class NoteProcessor:
    """Handles the lifecycle of a single note: cards, metadata, and state."""

    def __init__(
        self,
        ai: AI,
        anki: AnkiManager,
        state: StateManager,
        vault: VaultManager,
    ) -> None:
        self.settings: Settings = get_settings()

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
        has_no_excluded_tags = not any(
            tag in note.tags for tag in self.settings.EXCLUDE_TAGS
        )

        has_required_include_tag = not self.settings.INCLUDE_TAGS or any(
            tag in note.tags for tag in self.settings.INCLUDE_TAGS
        )

        return has_no_excluded_tags and has_required_include_tag

    def process_note(self, note: VaultNote) -> bool:
        """Generate flashcards for a single note. Returns success/failure."""
        try:
            if not note.content:
                logger.info(
                    "No content found in note with id: '%s'.",
                    note.id,
                )
                return True

            card_ids: list[int] | None = self._try_create_cards(note)

            if card_ids is None:
                return False

            if note.anki_cards:
                self.delete_old_cards(note.id, note.anki_cards)
                logger.info(
                    "Deleted %d cards of note with id: '%s'.",
                    len(note.anki_cards),
                    note.id,
                )

            self._vault.write_metadata(note, card_ids)
            new_path: str | None = self._vault.move_to(
                Path(note.path),
                self.settings.INBOX_FOLDER,
                self.settings.MAIN_NOTES_FOLDER,
            )
            if new_path is not None:
                note.path = new_path

            self._state.prepare_for_state(NoteInfo(vault_info=note, card_ids=card_ids))

            logger.info("Processed note with id: '%s'.", note.id)

            return True

        except AIInvalidOutput as exc:
            logger.error(
                "AI returned invalid flashcards for note '%s': %s",
                note.id,
                exc,
            )
            return False

        except AnkiError as exc:
            logger.exception(
                "Anki error of type %s while processing note with id '%s': %s",
                type(exc).__name__,
                note.id,
                exc,
            )
            return False

        except Exception:
            logger.exception(
                "Unexpected failure while processing note '%s'.",
                note.id,
            )
            return False

    def delete_old_cards(self, note_id: str, old_card_ids: list[int]) -> None:
        """Deletes all flash cards of note with given id"""
        current_cards: list[int] | None = self._state.delete_old_cards(
            note_id, old_card_ids
        )
        note_path: Path = Path(self._state.get_property_of(note_id, "path"))

        if not current_cards:
            self._vault.remove_property(note_path)

        for card_id in old_card_ids:
            self._anki.delete_card(card_id)
            self._vault.remove_list_item(note_path, "anki_cards", str(card_id))

    def _try_create_cards(self, note: VaultNote) -> list[int] | None:
        max_retries: int = self.settings.MAX_RETRIES_ON_ANKI_DUPLICATE_CARD

        for attempt in range(max_retries + 1):
            flash_cards: list[Flashcard] = self._ai.generate_note_cards(note)

            logger.info(
                "Generated %d flash cards for note with id: '%s'.",
                len(flash_cards),
                note.id,
            )
            try:
                ids: list[int] | None = self._anki.add_cards(note.id, flash_cards)
            except AnkiDuplicateNoteError:
                if attempt == max_retries:
                    logger.error(
                        "Failed to generate unique cards for note '%s' "
                        "after %d total attempts.",
                        note.id,
                        max_retries + 1,
                    )
                    return None

                logger.warning(
                    "Anki rejected generated cards for note '%s' as duplicates. "
                    "Regenerating (%d/%d).",
                    note.id,
                    attempt + 1,
                    max_retries,
                )
                continue

            return ids

        return None
