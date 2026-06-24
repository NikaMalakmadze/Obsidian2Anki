from pathlib import Path

from obsidian2anki.utils.helpers import process_note_content
from obsidian2anki.config import get_settings, Settings
from obsidian2anki.models import VaultNote

settings: Settings = get_settings()


class VaultManager:
    def __init__(self) -> None:
        self.root: Path = Path(settings.LOCAL_VAULT)
        self.ig_files: list[str] = settings.IGNORE_FILES
        self.ig_folders: list[str] = settings.IGNORE_FOLDERS

    def process_files(self) -> list[VaultNote]:
        notes: list[VaultNote] = []
        for item in self.root.iterdir():
            if not item.is_dir() or (item.is_dir() and item.name in self.ig_folders):
                continue
            for file in item.iterdir():
                vault_note: VaultNote | None = self._process_file(file)
                if not vault_note:
                    continue
                notes.append(vault_note)
        return notes

    def _process_file(self, file: Path) -> VaultNote | None:
        name: str = file.name.split(".")[0]
        if name in self.ig_files:
            return
        lines: list[str] = file.read_text().split("\n")
        tags: list[str] = lines[0].replace("#", "").split()
        content: str = process_note_content(" ".join(lines[2:]))
        return VaultNote(title=name, tags=tags, content=content)
