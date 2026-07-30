from frontmatter import Post
from pathlib import Path
import frontmatter
import logging
import uuid

from obsidian2anki.exceptions import ObsidianFolderDoesNotExists
from obsidian2anki.utils.helpers import process_note_content
from obsidian2anki import VAULT_NOTE_NECESSARY_PROPERTIES
from obsidian2anki.config import get_settings, Settings
from obsidian2anki.models import VaultNote


logger = logging.getLogger(__name__)


class VaultManager:
    def __init__(self) -> None:
        self.settings: Settings = get_settings()

        self.root: Path = Path(self.settings.LOCAL_VAULT)
        self.note_properties: tuple[str, ...] = VAULT_NOTE_NECESSARY_PROPERTIES

    def get_folder_notes(self, dir_name: str) -> list[VaultNote]:
        folder_path: Path = self.root / dir_name
        try:
            notes: list[VaultNote] = self._get_notes_recursively(folder_path, True)
            return notes
        except ObsidianFolderDoesNotExists:
            logger.exception(
                "Folder with path: '%s' does not exists", folder_path.resolve()
            )

    def remove_property(self, file: Path, property: str = "anki_cards") -> None:
        note: Post = frontmatter.loads(file.read_text(encoding="utf-8"))

        if property in note:
            del note[property]

        file.write_text(
            frontmatter.dumps(note).replace("\n\n", "\n", 1), encoding="utf-8"
        )

    def remove_list_item(
        self, file: Path, list_name: str, item: str
    ) -> list[str] | None:
        note: Post = frontmatter.loads(file.read_text(encoding="utf-8"))

        note_list_property: str = note.get(list_name, "")

        if not note_list_property:
            return

        note_list: list[str] = [i.strip() for i in note_list_property.split(",")]
        if item.strip() in note_list:
            note_list.remove(item.strip())

        if not note_list:
            return self.remove_property(file)

        note[list_name] = ", ".join(note_list)

        file.write_text(frontmatter.dumps(note), encoding="utf-8")

        return note_list

    def write_metadata(self, note: VaultNote, flash_card_ids: list[int]) -> None:
        file: Path = Path(note.path)

        lines: list[str] = file.read_text(encoding="utf-8").splitlines()

        lines.insert(2, f"anki_cards: {', '.join(map(str, flash_card_ids))}")

        file.write_text("\n".join(lines), encoding="utf-8")

        self._move_to(note, file, self.settings.MAIN_NOTES_FOLDER)

    def ensure_note_format(self, note_path: Path) -> None:
        lines: list[str] = note_path.read_text(encoding="utf-8").splitlines()

        tags: list[str] = [tag.removeprefix("#") for tag in lines.pop(0).split()]

        new_content: list[str] = [
            "---",
            f"id: {uuid.uuid4()!s}",
            "tags:",
            *[f"  - {tag}" for tag in tags],
            "---",
        ] + lines

        note_path.write_text("\n".join(new_content), encoding="utf-8")

    def has_metadata(self, note_path: Path) -> bool:
        note: Post = frontmatter.loads(note_path.read_text(encoding="utf-8"))
        note_keys: list[str] = list(note.keys())
        return all(
            needed_property in note_keys for needed_property in self.note_properties
        )

    def _move_to(
        self, note: VaultNote, note_file: Path, destination_folder: str
    ) -> None:
        destination_folder_path: Path = (
            Path(self.settings.LOCAL_VAULT) / destination_folder
        )
        note_path_str: str = str((destination_folder_path / note_file.name).resolve())

        if note.path != note_path_str:
            note_file.rename(destination_folder_path / note_file.name)
            note.path = note_path_str

    def _get_notes_recursively(
        self, root: Path, first_run: bool = False
    ) -> list[VaultNote]:
        if first_run and not root.exists():
            raise ObsidianFolderDoesNotExists(
                f"Folder with path: {root.resolve()} does not exists"
            )
        notes: list[VaultNote] = []

        for item in root.iterdir():
            if item.is_dir():
                notes.extend(self._get_notes_recursively(item))
            elif self._is_md(item):
                notes.append(self._process_file(item))
        return notes

    @staticmethod
    def _is_md(item: Path) -> bool:
        return item.is_file() and item.suffix == ".md"

    @staticmethod
    def _process_file(file: Path) -> VaultNote:
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
