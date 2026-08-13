from pathlib import Path
import logging

from obsidian2anki.core.vault_manager import VaultManager
from obsidian2anki.utils.enums import ExitCode


logger = logging.getLogger(__name__)


class NoteFormatterService:
    def __init__(self, vault: VaultManager) -> None:
        self._vault = vault

    def ensure_notes_format(
        self, dry_run: bool = False, recursive: bool = False
    ) -> ExitCode:
        main_notes_folder_path: Path = (
            Path(self._vault.settings.LOCAL_VAULT)
            / self._vault.settings.MAIN_NOTES_FOLDER
        )

        discovered_notes: list[Path] = self._vault.discover_notes(
            main_notes_folder_path, recursive
        )

        legacy_notes: list[Path] = [
            note_path
            for note_path in discovered_notes
            if not self._vault.has_metadata(note_path)
        ]

        total_notes: int = len(discovered_notes)

        logger.info(
            "Found %d notes requiring formatting out of %d notes in '%s' folder.",
            len(legacy_notes),
            total_notes,
            self._vault.settings.MAIN_NOTES_FOLDER,
        )

        for note_path in legacy_notes:
            logger.debug("Note needing formatting: '%s'", note_path.stem)

        if dry_run:
            logger.debug("Ended formatting on dry run.")
            return ExitCode.SUCCESS

        for note_path in legacy_notes:
            resolved_path: Path = note_path.resolve()
            self._vault.ensure_note_format(note_path)
            logger.info("Formatting file with path: '%s'.", resolved_path)

        return ExitCode.SUCCESS
