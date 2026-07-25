from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from pathlib import Path
from rich import box
import logging

from obsidian2anki.core.state_manager import StateManager
from obsidian2anki.core.anki_manager import AnkiManager
from obsidian2anki.config import Settings, get_settings

logger = logging.getLogger(__name__)
settings: Settings = get_settings()


@dataclass
class Statistic:
    """Result of a single statistic."""

    name: str
    value: int


class StatsService:
    def __init__(self, state: StateManager, anki: AnkiManager) -> None:
        self._state = state
        self._anki = anki
        self._local_vault: Path = Path(settings.LOCAL_VAULT)
        self._console = Console()

    def stats(self) -> None:
        inbox_folder_notes = self._folder_notes(settings.INBOX_FOLDER)
        main_folder_notes = self._folder_notes(settings.MAIN_NOTES_FOLDER)
        processed_notes = self._processed_notes()
        unprocessed_notes = self._unprocessed_notes()
        cards_count = self._anki_cards()

        table: Table = self._construct_table(
            (
                inbox_folder_notes,
                main_folder_notes,
                processed_notes,
                unprocessed_notes,
                cards_count,
            )
        )

        self._console.print(table)

    def _processed_notes(self) -> Statistic:
        processed_notes = self._state.get_state_items()

        logger.info("Found %d processed notes", len(processed_notes))

        for id, processed_note in processed_notes:
            logger.debug(
                "Processed note - '%s' with id - '%s'", processed_note[1].title, id
            )

        return Statistic("Processed notes", len(processed_notes))

    def _unprocessed_notes(self) -> Statistic:
        main_notes_folder_path: Path = self._local_vault / settings.MAIN_NOTES_FOLDER

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

        for unprocessed_note in unprocessed_notes:
            logger.debug("Unprocessed note: '%s'", unprocessed_note)

        return Statistic("Unprocessed Notes", len(unprocessed_notes))

    def _folder_notes(self, folder_name: str) -> Statistic:
        main_notes_folder = self._local_vault / folder_name

        total_notes: list[str] = [
            file.name.split(".")[0]
            for file in main_notes_folder.iterdir()
            if file.is_file()
        ]

        logger.info("Found %d notes in folder: '%s'", len(total_notes), folder_name)

        for note in total_notes:
            logger.debug("%s folder note: '%s'", folder_name, note)

        return Statistic(f"Notes In {folder_name} Folder", len(total_notes))

    def _anki_cards(self) -> Statistic:
        cards = self._anki.get_notes()

        logger.info("Found %d anki cards in deck: '%s'", len(cards), settings.DECK_NAME)

        return Statistic("Generated Cards", len(cards))

    @staticmethod
    def _construct_table(statistics: tuple[Statistic, ...]) -> Table:
        table = Table(
            title="[bold magenta]Statistics[/]",
            box=box.ROUNDED,
            highlight=True,
        )
        table.add_column("Statistic", style="bold magenta", no_wrap=True)
        table.add_column("Value")

        for statistic in statistics:
            table.add_row(statistic.name, str(statistic.value))

        return table
