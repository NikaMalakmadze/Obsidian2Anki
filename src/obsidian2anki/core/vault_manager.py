from pathlib import Path
import uuid

from obsidian2anki.config import get_settings, Settings
from obsidian2anki.models import VaultNote
from frontmatter import Post
import frontmatter

from obsidian2anki.utils.helpers import process_note_content

settings: Settings = get_settings()


class VaultManager:
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

    def remove_list_item(self, file: Path, list_name: str, item: str) -> None:
        note: Post = frontmatter.loads(file.read_text(encoding="utf-8"))

        note_list_property: str = note.get(list_name, "")

        if not note_list_property:
            return

        note_list: list[str] = [
            i.strip() for i in note_list_property.split(",") if i.strip() != item
        ]

        if not note_list:
            self.remove_property(file)
            return

        note[list_name] = ", ".join(note_list)

        file.write_text(frontmatter.dumps(note), encoding="utf-8")

    def write_metadata(self, note: VaultNote, flash_card_ids: list[int]) -> None:
        file: Path = Path(note.path)

        lines: list[str] = file.read_text(encoding="utf-8").splitlines()

        lines.insert(2, f"anki_cards: {', '.join(map(str, flash_card_ids))}")

        file.write_text("\n".join(lines), encoding="utf-8")

        self._move_to(note, file, settings.MAIN_NOTES_FOLDER)

    def ensure_note_format(self, note_path: Path) -> None:
        lines: list[str] = note_path.read_text(encoding="utf-8").splitlines()

        tags: list[str] = [tag.removeprefix("#") for tag in lines.pop(0).split()]

        new_content: list[str] = [
            "---",
            f"id: {str(uuid.uuid4())}",
            "tags:",
            *[f"  - {tag}" for tag in tags],
            "---",
        ] + lines

        note_path.write_text("\n".join(new_content), encoding="utf-8")

    def _move_to(
        self, note: VaultNote, note_file: Path, destination_folder: str
    ) -> None:
        destination_folder_path: Path = Path(settings.LOCAL_VAULT) / destination_folder
        note_path_str: str = str((destination_folder_path / note_file.name).resolve())

        if note.path != note_path_str:
            note_file.rename(destination_folder_path / note_file.name)
            note.path = note_path_str

    def _process_file(self, file: Path) -> VaultNote:
        note: Post = frontmatter.loads(file.read_text(encoding="utf-8"))

        anki_cards_property: int | str | list = note.get("anki_cards", [])

        if isinstance(anki_cards_property, int):
            anki_cards = [anki_cards_property]
        elif isinstance(anki_cards_property, str):
            anki_cards = [int(x.strip()) for x in anki_cards_property.split(",")]
        elif isinstance(anki_cards_property, list):
            anki_cards = [int(x) for x in anki_cards_property]
        else:
            anki_cards = []

        return VaultNote(
            id=note["id"],
            title=file.name.split(".")[0],
            tags=note.get("tags") if isinstance(note.get("tags"), list) else [],
            content=process_note_content(note.content.replace("\n", " ")),
            path=str(file.resolve()),
            anki_cards=anki_cards,
        )
