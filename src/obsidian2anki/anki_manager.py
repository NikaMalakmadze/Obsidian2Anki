import requests

from obsidian2anki.config import get_settings, Settings
from obsidian2anki.models import AnkiCard

settings: Settings = get_settings()


class AnkiManager:
    def __init__(self) -> None:
        self.anki_url = settings.ANKI_URL

    def connect(self, action: str, **params) -> dict:
        try:
            res = requests.post(
                settings.ANKI_URL,
                json={"action": action, "version": 6, "params": params},
            ).json()
            if len(res) != 2:
                raise Exception("Response has an unexpected number of fields.")
            if "error" not in res:
                raise Exception("Response is missing required error field.")
            if "result" not in res:
                raise Exception("Response is missing required result field.")
            if res["error"] is not None:
                raise Exception(res["error"])
            return res
        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to Anki. Is the Anki application open?")
            return None


m = AnkiManager()
card = AnkiCard(
    deck_name="Me",
    front="Bla",
    back="cat",
    tags=["vocab", "animals"],
)
m.connect("addNote", note=card.serialize())
