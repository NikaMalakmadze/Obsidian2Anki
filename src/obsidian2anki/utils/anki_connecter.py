from pydantic import ValidationError, BaseModel
from typing import Any
import subprocess
import requests
import logging
import shutil
import time

from obsidian2anki.exceptions import (
    AnkiActionError,
    AnkiConnectionError,
    AnkiDuplicateNoteError,
    AnkiResponseError,
)
from obsidian2anki.config import get_settings, Settings
from obsidian2anki.utils.type import Action


logger = logging.getLogger(__name__)


class AnkiConnecter:
    def __init__(self) -> None:
        self.settings: Settings = get_settings()
        self.anki_url = self.settings.ANKI_URL

    def connect(self, action: Action, **params) -> Any:
        if not self.anki_running():
            self.open_anki()

        payload = {"action": action, "version": 6, "params": params}
        try:
            response = requests.post(self.anki_url, json=payload)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise AnkiConnectionError(
                f"Could not reach AnkiConnect at {self.anki_url}."
            ) from exc

        try:
            response_data = response.json()
        except requests.JSONDecodeError as exc:
            raise AnkiResponseError("AnkiConnect returned invalid JSON.") from exc

        self._validate_res(response_data)

        return response_data["result"]

    def anki_running(self) -> bool:
        logger.debug("Trying to connect with anki.")
        try:
            response = requests.post(
                self.anki_url,
                json={"action": "version", "version": 6},
                timeout=1,
            )
            response.raise_for_status()
            data = response.json()
            logger.debug("Anki responded successfuly.")
            return data.get("error") is None
        except (requests.RequestException, ValueError):
            logger.debug("Error when trying to connect with anki.")
            return False

    def open_anki(self) -> None:
        path: str = shutil.which("anki")
        if path is None:
            logger.error("Could not find 'anki' executable.")
            return
        subprocess.Popen(
            [path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.info("Starting Anki...")
        for _ in range(20):
            if self.anki_running():
                logger.debug("Anki Started Sucessfuly")
                return
            time.sleep(1)

        logger.error("Anki did not start in time.")

    @staticmethod
    def _validate_params[T: BaseModel](
        validation_model: type[T], params: dict
    ) -> T | None:
        try:
            validated = validation_model.model_validate(params)
            return validated
        except ValidationError:
            logger.exception("Invalid Params.")

    @staticmethod
    def _validate_res(res: Any) -> None:
        if not isinstance(res, dict):
            raise AnkiResponseError(
                f"Expected a dictionary response, got {type(res).__name__}."
            )
        if set(res.keys()) != {"result", "error"}:
            raise AnkiResponseError(
                "Response must contain exactly 'result' and 'error'."
            )

        error = res["error"]
        if error is None:
            return

        error_message: str = str(error)
        if "cannot create note because it is a duplicate" in error_message.lower():
            raise AnkiDuplicateNoteError(error_message)

        raise AnkiActionError(error_message)
