from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from pathlib import Path
from rich import box
import logging

from obsidian2anki.core.state_manager import StateManager
from obsidian2anki.core.vault_manager import VaultManager
from obsidian2anki.core.anki_manager import AnkiManager
from obsidian2anki.models import VaultNote

logger = logging.getLogger(__name__)


@dataclass
class Statistic:
    """Result of a single statistic."""

    name: str
    value: int


class StatsService:
    def __init__(
        self, vault: VaultManager, state: StateManager, anki: AnkiManager
    ) -> None:
        self._anki = anki
        self._state = state
        self._vault = vault
        self._console = Console()
        self._local_vault: Path = vault.root

    def stats(self, recursive: bool = False) -> None:
        inbox_folder_notes = self._vault.get_folder_notes(
            self._state.settings.INBOX_FOLDER, recursive
        )
        main_folder_notes = self._vault.get_folder_notes(
            self._state.settings.MAIN_NOTES_FOLDER, recursive
        )

        inbox_folder_stats = self._folder_notes(
            self._state.settings.INBOX_FOLDER, inbox_folder_notes
        )
        main_folder_stats = self._folder_notes(
            self._state.settings.MAIN_NOTES_FOLDER, main_folder_notes
        )
        unprocessed_notes = self._unprocessed_notes(
            inbox_folder_notes, main_folder_notes
        )
        processed_notes = self._processed_notes()
        cards_count = self._anki_cards()

        table: Table = self._construct_table(
            (
                inbox_folder_stats,
                main_folder_stats,
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
                "Processed note - '%s' with id - '%s'", processed_note.title, id
            )

        return Statistic("Processed notes", len(processed_notes))

    def _unprocessed_notes(
        self, inbox_folder_notes: list[VaultNote], main_folder_notes: list[VaultNote]
    ) -> Statistic:
        inbox_unprocessed: list[str] = [note.title for note in inbox_folder_notes]
        main_unprocessed: list[str] = [
            note.title
            for note in main_folder_notes
            if not self._state.get_by_property("path", note.path)
        ]

        unprocessed_notes: list[str] = inbox_unprocessed + main_unprocessed

        logger.info(
            "Found %d unprocessed notes out of %d total notes in vault",
            len(unprocessed_notes),
            len(main_folder_notes) + len(inbox_folder_notes),
        )

        for unprocessed_note in unprocessed_notes:
            logger.debug("Unprocessed note: '%s'", unprocessed_note)

        return Statistic("Unprocessed Notes", len(unprocessed_notes))

    def _folder_notes(self, folder_name: str, notes: list[VaultNote]) -> Statistic:
        logger.info("Found %d notes in folder: '%s'", len(notes), folder_name)

        for note in notes:
            logger.debug("%s folder note: '%s'", folder_name, note)

        return Statistic(f"Notes In {folder_name} Folder", len(notes))

    def _anki_cards(self) -> Statistic:
        cards = self._anki.get_notes()

        logger.info(
            "Found %d anki cards in deck: '%s'",
            len(cards),
            self._state.settings.DECK_NAME,
        )

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
