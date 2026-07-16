from pathlib import Path
import logging

from obsidian2anki.core.note_processor import NoteProcessor
from obsidian2anki.core.state_manager import StateManager
from obsidian2anki.core.vault_manager import VaultManager
from obsidian2anki.config import Settings, get_settings
from obsidian2anki.models import VaultNote


logger = logging.getLogger(__name__)
settings: Settings = get_settings()


class MigrationService:
    def __init__(
        self, vault: VaultManager, state: StateManager, note_processor: NoteProcessor
    ) -> None:
        self._vault = vault
        self._state = state
        self._note_processor = note_processor

    def migrate(self) -> None:
        try:
            self._migrate()
        finally:
            self._state.save()

    def ensure_notes_format(self) -> None:
        main_notes_folder_path: Path = (
            Path(settings.LOCAL_VAULT) / settings.MAIN_NOTES_FOLDER
        )

        for file in main_notes_folder_path.iterdir():
            if file.is_file():
                self._vault.ensure_note_format(file)
                logger.info("Formatting file with path: '%s'.", str(file.resolve()))

    def _migrate(self) -> None:
        main_folder_notes: list[VaultNote] = self._vault.get_folder_notes(
            settings.MAIN_NOTES_FOLDER
        )
        if not main_folder_notes:
            logger.info("No notes found in '%s'.", settings.MAIN_NOTES_FOLDER)
            return

        logger.info(
            "Found %d notes in '%s'.",
            len(main_folder_notes),
            settings.MAIN_NOTES_FOLDER,
        )

        total_need_processing: int = sum(
            1
            for note in main_folder_notes
            if not (
                not self._note_processor.has_right_tags(note)
                or not self._note_processor.needs_processing(note)
            )
        )

        logger.info(
            "Found %d notes requiring processing out of %d notes in '%s' folder.",
            len(main_folder_notes),
            settings.MAIN_NOTES_FOLDER,
            total_need_processing,
        )

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
                total_need_processing,
                settings.MAIN_NOTES_FOLDER,
            )
