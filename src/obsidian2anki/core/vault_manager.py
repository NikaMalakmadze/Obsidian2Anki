from pathlib import Path
import uuid

from obsidian2anki.config import get_settings, Settings, BASE_DIR
from obsidian2anki.utils.note_processor import NoteProcessor
from obsidian2anki.models import VaultNote

settings: Settings = get_settings()


class VaultManager(NoteProcessor):
    def write_metadata(self, note: VaultNote, flash_card_ids: list[int]) -> None:
        file: Path = Path(note.path)

        lines: list[str] = file.read_text(encoding="utf-8").splitlines()

        lines[2] = "anki_processed: true"
        lines.insert(3, f"anki_cards: {', '.join(map(str, flash_card_ids))}")

        file.write_text("\n".join(lines), encoding="utf-8")

        processed_folder_path: Path = (
            Path(settings.LOCAL_VAULT) / settings.PROCESSED_FOLDER
        )

        file.rename(processed_folder_path / file.name)

    def ensure_note_uuids(self) -> None:
        main_notes_folder: Path = BASE_DIR / settings.MAIN_NOTES_FOLDER

        for file in main_notes_folder.iterdir():
            if not file.is_file():
                continue

            lines: list[str] = file.read_text(encoding="utf-8").splitlines()

            new_content: list[str] = [
                "---",
                f"id: {str(uuid.uuid4())}",
                "anki_processed: false",
                "---",
            ] + lines

            file.write_text("\n".join(new_content), encoding="utf-8")
