from pydantic import ValidationError, BaseModel
from typing import Any
import subprocess
import requests
import logging
import shutil
import time

from obsidian2anki.config import get_settings, Settings
from obsidian2anki.exceptions import AnkiValidationException
from obsidian2anki.utils.type import Action


settings: Settings = get_settings()
logger = logging.getLogger(__name__)


class AnkiConnecter:
    def __init__(self) -> None:
        self.anki_url = settings.ANKI_URL

    def connect(self, action: Action, **params) -> Any:
        if not self.anki_running():
            self.open_anki()

        try:
            payload = {"action": action, "version": 6, "params": params}
            response = requests.post(self.anki_url, json=payload)
            response.raise_for_status()
            result = response.json()
            self._validate_res(result)
            return result["result"]
        except (requests.RequestException, AnkiValidationException):
            logger.exception("Could not connect to Anki. Is the Anki application open?")
            return None

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
        subprocess.Popen([path])
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
    def _validate_res(res: dict[str, Any]) -> None:
        if len(res) != 2:
            raise AnkiValidationException(
                "Response has an unexpected number of fields."
            )
        if "error" not in res:
            raise AnkiValidationException("Response is missing required error field.")
        if "result" not in res:
            raise AnkiValidationException("Response is missing required result field.")
        if res["error"] is not None:
            raise AnkiValidationException(res["error"])
