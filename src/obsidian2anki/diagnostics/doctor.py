import logging

from obsidian2anki.diagnostics.enviroment_checker import EnviromentChecker
from obsidian2anki.diagnostics.runtime_checker import RuntimeCheker

logger = logging.getLogger(__name__)


class Doctor:
    """Check whether Obsidian2Anki is configured correctly."""

    def __init__(
        self, enviroment_checker: EnviromentChecker, runtime_checker: RuntimeCheker
    ) -> None:
        self._enviroment_checker = enviroment_checker
        self._runtime_checker = runtime_checker

    def run(self) -> None:
        """Run all diagnostic checks."""
        self._enviroment_checker.run()
