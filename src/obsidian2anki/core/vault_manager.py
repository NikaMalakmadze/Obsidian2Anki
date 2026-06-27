from pathlib import Path

from obsidian2anki.utils.note_processor import NoteProcessor
from obsidian2anki.config import get_settings, Settings
from obsidian2anki.models import VaultNote

settings: Settings = get_settings()


class VaultManager(NoteProcessor):
    def write_metadata(self, note: VaultNote, flash_card_ids: list[int]) -> None:
        file: Path = Path(note.path)

        lines: list[str] = file.read_text(encoding="utf-8").splitlines()

        new_content: list[str] = [
            "---",
            "anki_processed: true",
            f"anki_cards: {', '.join(map(str, flash_card_ids))}",
            "---",
        ] + lines

        file.write_text("\n".join(new_content), encoding="utf-8")

        processed_folder_path: Path = (
            Path(settings.LOCAL_VAULT) / settings.PROCESSED_FOLDER
        )

        file.rename(processed_folder_path / file.name)
