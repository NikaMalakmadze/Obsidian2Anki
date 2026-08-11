from pathlib import Path
import logging
import sys


from obsidian2anki.diagnostics.models import AppRuntimeCheck
from obsidian2anki.core.anki_manager import AnkiManager
from obsidian2anki.config import BASE_DIR, Settings
from obsidian2anki.core.ai import AI


logger = logging.getLogger(__name__)


class RuntimeChecker:
    MINIMUM_PYTHON_VERSION = (3, 12)

    def __init__(
        self, settings: Settings, anki: AnkiManager, ai: AI, base_dir: Path = BASE_DIR
    ) -> None:
        self._base_dir = base_dir
        self._settings = settings
        self._anki = anki
        self._ai = ai

    def check_runtime(self) -> list[AppRuntimeCheck]:
        """Run all diagnostic checks."""
        local_vault: Path = Path(self._settings.LOCAL_VAULT)

        results: list[AppRuntimeCheck] = [
            self._check_python_version(),
            self._check_file(".env File", ".env"),
            self._check_folder("Logs Folder", self._base_dir / "logs"),
            self._check_file("Logs File", self._base_dir / "logs/obsidian2anki.log"),
            self._check_folder("Local Vault", str(local_vault)),
            self._check_folder(
                "Inbox Folder", local_vault / self._settings.INBOX_FOLDER
            ),
            self._check_folder(
                "Main Notes Folder", local_vault / self._settings.MAIN_NOTES_FOLDER
            ),
            self._check_folder(
                "State Folder", self._base_dir / self._settings.STATE_FOLDER
            ),
            self._check_file("Prompt File", self._settings.PROMPT_FILE),
            self._check_api_key(self._settings.API_KEY),
        ]
        anki_result = self._check_anki()
        results.append(anki_result)

        if anki_result.passed:
            results.append(self._check_anki_deck())
        else:
            results.append(
                AppRuntimeCheck(
                    "Anki Deck",
                    False,
                    "Skipped because Anki is unreachable.",
                )
            )

        return results

    def _check_python_version(self) -> AppRuntimeCheck:
        current_version = sys.version_info[:3]

        current = ".".join(map(str, current_version))

        if current_version < self.MINIMUM_PYTHON_VERSION:
            required = ".".join(map(str, self.MINIMUM_PYTHON_VERSION))
            return AppRuntimeCheck(
                check="Python Version",
                passed=False,
                message=(
                    f"Python {current} detected; "
                    f"Python {required} or newer is required."
                ),
            )
        return AppRuntimeCheck(
            "Python Version", True, f"Python {current} is supported."
        )

    def _check_file(self, check_name: str, file_name: str) -> AppRuntimeCheck:
        _file = self._base_dir / file_name
        is_file: bool = _file.is_file()
        return AppRuntimeCheck(
            check_name,
            is_file,
            f"{file_name} file found at {_file}"
            if is_file
            else f"No {file_name} file was found at {_file}",
        )

    def _check_anki(self) -> AppRuntimeCheck:
        is_running: bool = self._anki.anki_running()
        return AppRuntimeCheck(
            "Anki",
            is_running,
            "Anki is running"
            if is_running
            else "Anki is not running, please open it manually or check its url in .env file",
        )

    def _check_anki_deck(self) -> AppRuntimeCheck:
        is_deck: bool = self._settings.DECK_NAME in self._anki.get_decks()
        return AppRuntimeCheck(
            "Anki Deck",
            is_deck,
            "Anki deck exists" if is_deck else "Anki deck does not exists",
        )

    def _check_api_key(self, api_key: str) -> AppRuntimeCheck:
        is_valid: bool = self._ai.validate_key(api_key)
        return AppRuntimeCheck(
            "API key",
            is_valid,
            "API key is correct" if is_valid else "API key is incorrect",
        )

    @staticmethod
    def _check_folder(
        folder_name: str, folder_path: str | Path | None
    ) -> AppRuntimeCheck:
        if folder_path is None:
            return AppRuntimeCheck(
                folder_name,
                False,
                f"{folder_name} is not configured.",
            )

        is_str_path: bool = isinstance(folder_path, str)
        if is_str_path and not folder_path.strip():
            return AppRuntimeCheck(
                folder_name,
                False,
                f"{folder_name} is not configured.",
            )

        path = Path(folder_path) if is_str_path else folder_path
        if not path.exists():
            return AppRuntimeCheck(
                folder_name, False, f"{folder_name} does not exist: {path}"
            )
        if not path.is_dir():
            return AppRuntimeCheck(
                folder_name, False, f"{folder_name} is not a directory: {path}"
            )

        return AppRuntimeCheck(folder_name, True, f"{folder_name} found: {path}")
