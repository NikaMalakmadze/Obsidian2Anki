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

    def is_changed(self) -> bool:
        return len(self._temp_data) > 0

    def in_state(self, note_title: str, note_content: str) -> bool:
        content_hash: str = sha256(note_content.encode("utf-8")).hexdigest()
        return (
            note_title in self._state
            and content_hash == self._state[note_title].content_hash
        )

    def update_state(self, note: NoteInfo) -> None:
        content_hash: str = sha256(note.vault_info.content.encode("utf-8")).hexdigest()

        curr_datetime: datetime = datetime.now(timezone.utc)

        state_note: StateNote = StateNote(
            path=note.vault_info.path,
            anki_note_ids=note.card_ids,
            processed_at=curr_datetime.isoformat(),
            updated_at=curr_datetime.isoformat(),
            card_count=len(note.card_ids),
            content_hash=content_hash,
        )

        self._temp_data.append((note.vault_info.title, state_note))

    def set_state(self) -> None:
        for k, v in self._temp_data:
            self._state[k] = v

        self.state_file.write_text(
            json.dumps({k: v.model_dump() for k, v in self._state.items()}, indent=4)
        )

        self._temp_data = []


StateManager().set_state(
    [
        NoteInfo(
            vault_info={
                "title": "Python Notes",
                "tags": ["python", "pydantic"],
                "content": "Some note content",
                "path": "/notes/python.md",
            },
            card_ids=[1, 2, 3],
        )
    ]
)
