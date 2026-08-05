from frontmatter import Post
from pathlib import Path
import frontmatter
import logging
import uuid

from obsidian2anki.constants import VAULT_NOTE_NECESSARY_PROPERTIES
from obsidian2anki.exceptions import ObsidianFolderDoesNotExists
from obsidian2anki.utils.helpers import process_note_content
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

    def remove_property(self, note_path: Path, property: str = "anki_cards") -> None:
        frontmatter_post: Post = self._get_frontmatter(note_path)

        if property in frontmatter_post:
            del frontmatter_post[property]

        self._write_frontmatter(note_path, frontmatter_post)

    def remove_list_item(
        self, note_path: Path, list_name: str, item: str
    ) -> list[str] | None:
        frontmatter_post: Post = self._get_frontmatter(note_path)

        note_list_property: str = frontmatter_post.get(list_name, "")

        if not note_list_property:
            return

        note_list: list[str] = [i.strip() for i in note_list_property.split(",")]
        if item.strip() in note_list:
            note_list.remove(item.strip())

        if not note_list:
            return self.remove_property(note_path)

        frontmatter_post[list_name] = ", ".join(note_list)

        self._write_frontmatter(note_path, frontmatter_post)

        return note_list

    def write_metadata(self, note: VaultNote, flash_card_ids: list[int]) -> None:
        note_path: Path = Path(note.path)

        old_frontmatter_post: Post = self._get_frontmatter(note_path)

        metadata = {
            "id": old_frontmatter_post.get("id", f"{uuid.uuid4()!s}"),
            "tags": old_frontmatter_post.get("tags", []),
            "anki_cards": ", ".join(map(str, flash_card_ids)),
        }

        new_frontmatter_post: Post = frontmatter.Post(
            content=old_frontmatter_post.content, **metadata
        )
        self._write_frontmatter(note_path, new_frontmatter_post)

    def ensure_note_format(self, note_path: Path) -> None:
        note_content_lines: list[str] = note_path.read_text(
            encoding="utf-8"
        ).splitlines()
        tags_line: str = note_content_lines.pop(0)
        tags: list[str] = [tag.removeprefix("#") for tag in tags_line.split()]

        metadata: dict[str, str] = {
            "id": f"{uuid.uuid4()!s}",
            "tags": tags,
        }

        frontmatter_post: Post = frontmatter.Post(
            content="\n".join(note_content_lines), **metadata
        )

        self._write_frontmatter(note_path, frontmatter_post)

    def has_metadata(self, note_path: Path) -> bool:
        frontmatter_post: Post = self._get_frontmatter(note_path)
        note_keys: list[str] = list(frontmatter_post.keys())
        return all(
            needed_property in note_keys for needed_property in self.note_properties
        )

    def move_to(self, note: VaultNote, destination_folder: str) -> None:
        destination_folder_path: Path = self.root / destination_folder
        note_file: Path = Path(note.path)
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

    def _process_file(self, note_path: Path) -> VaultNote:
        frontmatter_post: Post = self._get_frontmatter(note_path)

        anki_cards_property: int | str | list = frontmatter_post.get("anki_cards", [])

        if isinstance(anki_cards_property, int):
            anki_cards = [anki_cards_property]
        elif isinstance(anki_cards_property, str):
            anki_cards = [int(x.strip()) for x in anki_cards_property.split(",")]
        elif isinstance(anki_cards_property, list):
            anki_cards = [int(x) for x in anki_cards_property]
        else:
            anki_cards = []

        return VaultNote(
            id=frontmatter_post["id"],
            title=note_path.name.split(".")[0],
            tags=frontmatter_post.get("tags")
            if isinstance(frontmatter_post.get("tags"), list)
            else [],
            content=process_note_content(frontmatter_post.content.replace("\n", " ")),
            path=str(note_path.resolve()),
            anki_cards=anki_cards,
        )

    @staticmethod
    def _is_md(item: Path) -> bool:
        return item.is_file() and item.suffix == ".md"

    @staticmethod
    def _get_frontmatter(note_path: Path) -> Post:
        return frontmatter.loads(note_path.read_text(encoding="utf-8"))

    @staticmethod
    def _write_frontmatter(note_path: Path, frontmatter_post: Post) -> None:
        serialized_note = frontmatter.dumps(frontmatter_post, sort_keys=False)
        serialized_note = serialized_note.replace("---\n\n", "---\n", 1)
        note_path.write_text(serialized_note, encoding="utf-8")
