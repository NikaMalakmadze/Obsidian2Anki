import logging

from obsidian2anki.core.note_processor import NoteProcessor
from obsidian2anki.core.state_manager import StateManager
from obsidian2anki.core.vault_manager import VaultManager
from obsidian2anki.models import VaultNote


logger = logging.getLogger(__name__)


class MigrationService:
    def __init__(
        self, vault: VaultManager, state: StateManager, note_processor: NoteProcessor
    ) -> None:
        self._vault = vault
        self._state = state
        self._note_processor = note_processor

    def migrate(self, dry_run: bool = False) -> None:
        try:
            self._migrate(dry_run)
        finally:
            self._state.save()

    def _migrate(self, dry_run: bool = False) -> None:
        main_folder_notes: list[VaultNote] = self._vault.get_folder_notes(
            self._vault.settings.MAIN_NOTES_FOLDER
        )
        if not main_folder_notes:
            logger.info(
                "No notes found in '%s'.", self._vault.settings.MAIN_NOTES_FOLDER
            )
            return

        logger.info(
            "Found %d notes in '%s'.",
            len(main_folder_notes),
            self._vault.settings.MAIN_NOTES_FOLDER,
        )

        notes_needing_processing: list[str] = [
            note.title
            for note in main_folder_notes
            if not (
                not self._note_processor.has_right_tags(note)
                or not self._note_processor.needs_processing(note)
            )
        ]

        logger.info(
            "Found %d notes requiring processing out of %d notes in '%s' folder.",
            len(notes_needing_processing),
            len(main_folder_notes),
            self._vault.settings.MAIN_NOTES_FOLDER,
        )

        for note in notes_needing_processing:
            logger.debug("Note needing processing: '%s'", note)

        if dry_run:
            logger.debug("Ended migration on dry run.")
            return

        c: int = 0

        for note in main_folder_notes:
            if not self._note_processor.has_right_tags(
                note
            ) or not self._note_processor.needs_processing(note):
                continue

            if not self._note_processor.process_note(note):
                break

            c += 1

            logger.info(
                "Processed note %d/%d from '%s' folder.",
                c,
                len(notes_needing_processing),
                self._vault.settings.MAIN_NOTES_FOLDER,
            )
