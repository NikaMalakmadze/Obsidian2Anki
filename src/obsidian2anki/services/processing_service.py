import logging

from obsidian2anki.core.note_processor import NoteProcessor
from obsidian2anki.core.state_manager import StateManager
from obsidian2anki.core.vault_manager import VaultManager
from obsidian2anki.utils.enums import ExitCode
from obsidian2anki.models import VaultNote


logger = logging.getLogger(__name__)


class ProcessingService:
    def __init__(
        self, vault: VaultManager, state: StateManager, note_processor: NoteProcessor
    ) -> None:
        self._vault = vault
        self._state = state
        self._note_processor = note_processor

    def process(self, dry_run: bool = False, recursive: bool = False) -> ExitCode:
        try:
            return self._process(dry_run, recursive)
        finally:
            self._state.save()

    def _process(self, dry_run: bool = False, recursive: bool = False) -> ExitCode:
        notes: list[VaultNote] = self._vault.get_folder_notes(
            self._vault.settings.INBOX_FOLDER, recursive
        )

        if not notes:
            logger.info("No notes found in '%s'.", self._vault.settings.INBOX_FOLDER)
            return ExitCode.SUCCESS

        eligible_notes: list[VaultNote] = [
            note for note in notes if self._note_processor.has_right_tags(note)
        ]

        if not eligible_notes:
            logger.info(
                "No eligible notes found in '%s'.",
                self._vault.settings.INBOX_FOLDER,
            )
            return ExitCode.SUCCESS

        logger.info(
            "Found %d notes in '%s'.",
            len(eligible_notes),
            self._vault.settings.INBOX_FOLDER,
        )

        if dry_run:
            for note in eligible_notes:
                logger.info("Note needing processing: '%s'.", note.title)

            logger.debug("Ended processing on dry run.")
            return ExitCode.SUCCESS

        for note in notes:
            self._note_processor.process_note(note)

        return ExitCode.SUCCESS
