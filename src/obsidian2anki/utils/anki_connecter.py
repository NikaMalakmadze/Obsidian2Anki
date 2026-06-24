from pydantic import ValidationError
from typing import Any
import requests

from obsidian2anki.config import get_settings, Settings
from obsidian2anki.utils.type import Action


settings: Settings = get_settings()


class AnkiConnecter:
    def __init__(self) -> None:
        self.anki_url = settings.ANKI_URL

    def connect(self, action: Action, **params) -> Any:
        try:
            payload = {"action": action, "version": 6, "params": params}
            res = requests.post(settings.ANKI_URL, json=payload).json()
            self._validate_res(res)
            return res["result"]
        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to Anki. Is the Anki application open?")
        return None

    @staticmethod
    def _validate_params[T](validation_model: T, params: dict) -> T:
        try:
            validated = validation_model.model_validate(params)
            return validated
        except ValidationError:
            print("Error: Invalid Params.")
            return None

    @staticmethod
    def _validate_res(res):
        if len(res) != 2:
            raise Exception("Response has an unexpected number of fields.")
        if "error" not in res:
            raise Exception("Response is missing required error field.")
        if "result" not in res:
            raise Exception("Response is missing required result field.")
        if res["error"] is not None:
            raise Exception(res["error"])
