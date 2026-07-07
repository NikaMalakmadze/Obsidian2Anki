from pathlib import Path

from obsidian2anki.utils.helpers import process_note_content
from obsidian2anki.config import get_settings, Settings
from obsidian2anki.models import VaultNote

settings: Settings = get_settings()


class NoteProcessor:
    def __init__(self) -> None:
        self.root: Path = Path(settings.LOCAL_VAULT)

    def get_inbox_notes(self, dir_name: str) -> list[VaultNote]:
        notes: list[VaultNote] = [
            self._process_file(item)
            for item in (self.root / dir_name).iterdir()
            if item.is_file()
        ]
        return notes

    def _process_file(self, file: Path) -> VaultNote:
        name: str = file.name.split(".")[0]
        lines: list[str] = file.read_text(encoding="utf-8").splitlines()
        id: str = lines[1].split(":")[1]
        tags: list[str] = lines[0].replace("#", "").split()
        content: str = process_note_content(" ".join(lines[2:]))
        return VaultNote(
            id=id,
            title=name,
            tags=tags,
            content=content,
            raw_content=lines,
            path=str(file.resolve()),
        )
