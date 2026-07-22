from rich.markdown import Markdown
from dataclasses import dataclass
from rich.console import Console
from typing import Sequence
from pathlib import Path
import logging
import sys

from obsidian2anki.config import BASE_DIR, Settings, get_settings
from obsidian2anki.core.ai import AI

logger = logging.getLogger(__name__)
settings: Settings = get_settings()


@dataclass
class CheckResult:
    """Result of a single diagnostic check."""

    passed: bool
    message: str


class Doctor:
    """Check whether Obsidian2Anki is configured correctly."""

    MINIMUM_PYTHON_VERSION = (3, 12)

    def __init__(self, ai: AI, base_dir: Path = BASE_DIR) -> None:
        self._base_dir = base_dir
        self._console = Console()
        self._ai = ai

    def run(self) -> None:
        """Run all diagnostic checks."""
        results: dict[str, CheckResult] = {
            "Python Version": self._check_python_version(),
            ".env Is File": self._check_env_file(),
            "Local Vault": self._check_folder(settings.LOCAL_VAULT, "Local Vault"),
            "Inbox Folder": self._check_vault_folder(settings.INBOX_FOLDER),
            "Main Notes Folder": self._check_vault_folder(settings.MAIN_NOTES_FOLDER),
            "State Folder": self._check_folder(
                self._base_dir / settings.STATE_FOLDER, "State Folder"
            ),
            "API key": self._check_api_key(settings.API_KEY),
        }

        markdown = self._construct_md(results)

        self._console.print(markdown)

        return self._passed_checks(results.values())

    def _check_python_version(self) -> CheckResult:
        current_version = sys.version_info[:3]

        current = ".".join(map(str, current_version))

        if current_version < self.MINIMUM_PYTHON_VERSION:
            required = ".".join(map(str, self.MINIMUM_PYTHON_VERSION))
            return CheckResult(
                passed=False,
                message=(
                    f"Python {current} detected; "
                    f"Python {required} or newer is required."
                ),
            )
        return CheckResult(True, f"Python {current} is supported.")

    def _check_env_file(self) -> CheckResult:
        env_file = self._base_dir / ".env"
        is_file: bool = env_file.is_file()
        return CheckResult(
            is_file,
            f"Environment file found at {env_file}"
            if is_file
            else f"No .env file was found at {env_file}",
        )

    def _check_vault_folder(self, folder_name: str) -> CheckResult:
        if not self._check_folder(settings.LOCAL_VAULT, "Local Vault").passed:
            return CheckResult(False, "Local vault does not exists")

        return self._check_folder(Path(settings.LOCAL_VAULT) / folder_name, folder_name)

    def _check_api_key(self, api_key: str) -> CheckResult:
        is_valid: bool = self._ai.validate_key(api_key)
        return CheckResult(
            is_valid, "API key is correct" if is_valid else "API key is incorrect"
        )

    @staticmethod
    def _check_folder(folder_path: str, folder_name: str) -> CheckResult:
        is_str_path: bool = isinstance(folder_path, str)
        if is_str_path and not folder_path:
            return CheckResult(False, "{folder_name} is not configured.")

        path = Path(folder_path) if is_str_path else folder_path
        if not path.exists():
            return CheckResult(False, f"{folder_name} does not exist: {path}")
        if not path.is_dir():
            return CheckResult(False, f"{folder_name} is not a directory: {path}")

        return CheckResult(True, f"{folder_name} found: {path}")

    @staticmethod
    def _passed_checks(results: Sequence[CheckResult]) -> bool:
        return all(result.passed for result in results)

    @staticmethod
    def _construct_md(results: dict[str, CheckResult]) -> Markdown:
        results_list: list[str] = [
            f" - {'✅' if result.passed else '❌ '} {name}: {result.message}"
            for name, result in results.items()
        ]

        markdown_content: str = f"# Doctor Results:\n{'\n'.join(results_list)}"

        return Markdown(markdown_content)
