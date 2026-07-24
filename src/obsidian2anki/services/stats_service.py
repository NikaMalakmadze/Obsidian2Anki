from pathlib import Path
import logging

from obsidian2anki.core.state_manager import StateManager
from obsidian2anki.core.anki_manager import AnkiManager
from obsidian2anki.config import Settings, get_settings

logger = logging.getLogger(__name__)
settings: Settings = get_settings()


class StatsService:
    def __init__(self, state: StateManager, anki: AnkiManager) -> None:
        self._state = state
        self._anki = anki

    def stats(self) -> None:
        self._processed_notes()
        self._anki_cards()

    def _processed_notes(self) -> None:
        main_notes_folder_path: Path = (
            Path(settings.LOCAL_VAULT) / settings.MAIN_NOTES_FOLDER
        )

        unprocessed_notes: list[str] = [
            file.name.split(".")[0]
            for file in main_notes_folder_path.iterdir()
            if file.is_file()
            and not self._state.get_by_property("path", str(file.resolve()))
        ]

        total_notes: int = len(
            [file.is_file() for file in main_notes_folder_path.iterdir()]
        )

        logger.info(
            "Found %d unprocessed notes out of %d processed notes in '%s' folder.",
            len(unprocessed_notes),
            total_notes,
            settings.MAIN_NOTES_FOLDER,
        )

    def _anki_cards(self) -> None:
        cards = self._anki.get_notes()

        logger.info("Found %d anki cards", len(cards))
