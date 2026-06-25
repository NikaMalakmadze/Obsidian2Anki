from pathlib import Path

from obsidian2anki.utils.helpers import process_note_content
from obsidian2anki.config import get_settings, Settings
from obsidian2anki.models import VaultNote

settings: Settings = get_settings()


class NoteProcessor:
    def __init__(self) -> None:
        self.root: Path = Path(settings.LOCAL_VAULT)

    def _process_files(self, dir: Path) -> list[VaultNote]:
        notes: list[VaultNote] = [
            self._process_file(item)
            for item in (self.root / dir).iterdir()
            if item.is_file()
        ]
        return notes

    def _process_file(self, file: Path) -> VaultNote:
        name: str = file.name.split(".")[0]
        lines: list[str] = file.read_text().split("\n")
        tags: list[str] = lines[0].replace("#", "").split()
        content: str = process_note_content(" ".join(lines[2:]))
        return VaultNote(title=name, tags=tags, content=content)
