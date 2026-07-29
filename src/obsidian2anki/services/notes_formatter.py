from pathlib import Path
import logging

from obsidian2anki.core.vault_manager import VaultManager
from obsidian2anki.config import Settings, get_settings


logger = logging.getLogger(__name__)
settings: Settings = get_settings()


class NoteFormatterService:
    def __init__(self, vault: VaultManager) -> None:
        self._vault = vault

    def ensure_notes_format(self, dry_run: bool = False) -> None:
        main_notes_folder_path: Path = (
            Path(settings.LOCAL_VAULT) / settings.MAIN_NOTES_FOLDER
        )

        legacy_notes: list[str] = [
            file.name.split(".")[0]
            for file in main_notes_folder_path.iterdir()
            if file.is_file() and not self._vault.has_metadata(file)
        ]

        total_notes: int = len(
            [file.is_file() for file in main_notes_folder_path.iterdir()]
        )

        logger.info(
            "Found %d notes requiring formatting out of %d notes in '%s' folder.",
            len(legacy_notes),
            total_notes,
            settings.MAIN_NOTES_FOLDER,
        )

        for note in legacy_notes:
            logger.debug("Note needing formatting: '%s'", note)

        if dry_run:
            logger.debug("Ended formatting on dry run.")
            return

        for file in main_notes_folder_path.iterdir():
            resolved_path: Path = file.resolve()
            if file.is_file() and not self._vault.has_metadata(file):
                self._vault.ensure_note_format(file)
                logger.info("Formatting file with path: '%s'.", resolved_path)
                continue
            logger.info("Skipping formatted file with path: '%s'.", resolved_path)
