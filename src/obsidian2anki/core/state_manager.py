from datetime import datetime, UTC
from hashlib import sha256
from pathlib import Path
from typing import Any
import json

from obsidian2anki.config import Settings, get_settings, BASE_DIR
from obsidian2anki.utils.type import StateNoteProperties
from obsidian2anki.models import StateNote, NoteInfo


class StateManager:
    def __init__(self) -> None:
        self.settings: Settings = get_settings()

        self._state: dict[str, StateNote] = {}

        self.state_folder: Path = BASE_DIR / self.settings.STATE_FOLDER
        self.state_folder.mkdir(parents=True, exist_ok=True)

        self.state_file: Path = self.state_folder / "state.json"
        self.state_file.touch(exist_ok=True)

        self._temp_data: list[tuple[str, StateNote]] = []
        self._is_changed: bool = False
        self._load_state()

    def clear_state(self) -> None:
        self._state = {}
        self._is_changed = True
        self.save()

    def in_state(self, note_id: str) -> bool:
        return note_id in self._state

    def has_changed(self, note_id: str, note_title: str, note_content: str) -> bool:
        note: StateNote | None = self._state.get(note_id)
        if not note:
            return False

        content_hash: str = sha256(note_content.encode("utf-8")).hexdigest()

        is_changed: bool = note.content_hash != content_hash or note.title != note_title

        if is_changed:
            note.updated_at = datetime.now(UTC).isoformat()

        return is_changed

    def get_state_items(self) -> list[tuple[str, StateNote]]:
        return list(self._state.items())

    def get_property_of(self, id: str, property: StateNoteProperties):
        note: StateNote | None = self._state.get(id)
        if not note:
            return
        return getattr(note, property)

    def get_by_property(
        self, search_by: StateNoteProperties, search_value: Any
    ) -> StateNote | None:
        for item in self._state.values():
            if getattr(item, search_by, None) == search_value:
                return item

    def delete_state_item(self, id: str) -> None:
        if id in self._state:
            del self._state[id]
            self._is_changed = True
            self.save()

    def prepare_for_state(self, note: NoteInfo) -> None:
        content_hash: str = sha256(note.vault_info.content.encode("utf-8")).hexdigest()

        curr_datetime: datetime = datetime.now(UTC)

        state_note: StateNote = StateNote(
            title=note.vault_info.title,
            path=note.vault_info.path,
            anki_note_ids=note.card_ids,
            processed_at=curr_datetime.isoformat(),
            updated_at=curr_datetime.isoformat(),
            card_count=len(note.card_ids),
            content_hash=content_hash,
        )

        self._temp_data.append((note.vault_info.id, state_note))

        self._is_changed = True

    def delete_card(self, card_id: int) -> str | None:
        note_id: str | None = None
        for id, note_info in self._state.items():
            if card_id not in note_info.anki_note_ids:
                continue

            curr_datetime: str = datetime.now(UTC).isoformat()
            note_info.updated_at = curr_datetime
            note_info.anki_note_ids.remove(card_id)
            note_info.card_count -= 1
            note_id = id

        if note_id:
            self._is_changed = True
            self.save()
        return note_id

    def delete_note_cards(self, note_id: str) -> bool:
        note: StateNote | None = self._state.get(note_id)
        if not note:
            return False

        curr_datetime: str = datetime.now(UTC).isoformat()
        note.updated_at = curr_datetime
        note.anki_note_ids = []

        self._is_changed = True
        self.save()

        return True

    def delete_old_cards(self, note_id: str, old_cards: list[int]) -> list[int] | None:
        note: StateNote | None = self._state.get(note_id)
        if not note:
            return None

        curr_datetime: str = datetime.now(UTC).isoformat()
        note.updated_at = curr_datetime

        filtered_note_ids: list[int] = [
            id for id in note.anki_note_ids if id not in old_cards
        ]
        note.anki_note_ids = filtered_note_ids

        self._is_changed = True
        self.save()

        return filtered_note_ids

    def save(self) -> None:
        if not self._is_changed:
            return

        self._extend_state()

        self.state_file.write_text(
            json.dumps(
                {k: v.model_dump() for k, v in self._state.items()},
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        self._temp_data = []
        self._is_changed = False

    def _extend_state(self) -> None:
        for k, v in self._temp_data:
            self._state[k] = v

    def _load_state(self) -> None:
        plain_text: str = self.state_file.read_text(encoding="utf-8")
        plain_json: dict = json.loads(plain_text) if plain_text else {}
        self._state = {k: StateNote.model_validate(v) for k, v in plain_json.items()}
