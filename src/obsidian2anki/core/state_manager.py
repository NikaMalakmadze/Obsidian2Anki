from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json

from obsidian2anki.config import Settings, get_settings, BASE_DIR
from obsidian2anki.models import StateNote, NoteInfo

settings: Settings = get_settings()


class StateManager:
    def __init__(self) -> None:
        self._state: dict[str, StateNote] = {}
        self.state_folder: Path = BASE_DIR / settings.STATE_FOLDER
        self.state_file: Path = self.state_folder / "state.json"
        self._temp_data: list[tuple[str, StateNote]] = []
        self._is_changed: bool = False
        self._load_state()

    @property
    def state(self) -> dict[str, StateNote]:
        return self._state

    def clear_state(self) -> None:
        self._state = {}
        self._is_changed = True
        self.set_state()

    def in_state(self, note_id: str) -> bool:
        return note_id in self._state

    def has_changed(self, note_id: str, note_title: str, note_content: str) -> bool:
        note: StateNote | None = self._state.get(note_id)
        if not note:
            return False

        content_hash: str = sha256(note_content.encode("utf-8")).hexdigest()

        return note.content_hash != content_hash or note.title != note_title

    def prepare_for_state(self, note: NoteInfo) -> None:
        content_hash: str = sha256(note.vault_info.content.encode("utf-8")).hexdigest()

        curr_datetime: datetime = datetime.now(timezone.utc)

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

    def delete_card(self, card_id: int) -> bool:
        found: bool = False
        for note_info in self._state.values():
            if card_id not in note_info.anki_note_ids:
                continue

            curr_datetime: str = datetime.now(timezone.utc).isoformat()
            note_info.updated_at = curr_datetime
            note_info.anki_note_ids.remove(card_id)
            found = True

        if found:
            self._is_changed = True
            self.set_state()
        return found

    def delete_note_cards(self, note_id: str) -> bool:
        note: StateNote | None = self._state.get(note_id)
        if not note:
            return False

        curr_datetime: str = datetime.now(timezone.utc).isoformat()
        note.updated_at = curr_datetime
        note.anki_note_ids = []

        self._is_changed = True
        self.set_state()

        return True

    def set_state(self) -> None:
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
