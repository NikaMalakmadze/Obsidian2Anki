from frontmatter import Post
from pathlib import Path
import frontmatter

from obsidian2anki.utils.helpers import process_note_content
from obsidian2anki.config import get_settings, Settings
from obsidian2anki.models import VaultNote

settings: Settings = get_settings()


class NoteProcessor:
    def __init__(self) -> None:
        self.root: Path = Path(settings.LOCAL_VAULT)

    def get_folder_notes(self, dir_name: str) -> list[VaultNote]:
        notes: list[VaultNote] = [
            self._process_file(item)
            for item in (self.root / dir_name).iterdir()
            if item.is_file()
        ]
        return notes

    def remove_property(self, file: Path, property: str = "anki_cards") -> None:
        note: Post = frontmatter.loads(file.read_text(encoding="utf-8"))

        if property in note:
            del note[property]

        file.write_text(
            frontmatter.dumps(note).replace("\n\n", "\n", 1), encoding="utf-8"
        )

    def _process_file(self, file: Path) -> VaultNote:
        note: Post = frontmatter.loads(file.read_text(encoding="utf-8"))

        return VaultNote(
            id=note["id"],
            title=file.name.split(".")[0],
            tags=note.get("tags") if isinstance(note.get("tags"), list) else [],
            content=process_note_content(note.content.replace("\n", " ")),
            path=str(file.resolve()),
            anki_cards=[int(x.strip()) for x in note.get("anki_cards", "").split(",")]
            if note.get("anki_cards")
            else [],
        )
