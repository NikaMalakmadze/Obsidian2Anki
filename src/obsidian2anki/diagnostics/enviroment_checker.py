import logging

from pydantic_core import ErrorDetails
from pydantic import ValidationError

from obsidian2anki.config import Settings, get_settings


logger = logging.getLogger(__name__)


class EnviromentChecker:
    def run(self) -> None:
        self._check_env()

    def _check_env(self):
        try:
            settings: Settings = get_settings()
        except ValidationError as e:
            errors: list[ErrorDetails] = e.errors(include_input=True)

            for error in errors:
                error_loc: str = error.get("loc")[0]
                if error.get("type") == "missing":
                    logger.warning(
                        "Field with name '%s' is missing in env file.", error_loc
                    )
