import logging

from obsidian2anki.diagnostics.columns import (
    environment_table_columns,
    runtime_table_columns,
)
from obsidian2anki.diagnostics.environment_checker import EnvironmentChecker
from obsidian2anki.diagnostics.runtime_checker import RuntimeChecker
from obsidian2anki.diagnostics.output_manager import OutputManager
from obsidian2anki.diagnostics.models import AppEnvironmentError
from obsidian2anki.core.anki_manager import AnkiManager
from obsidian2anki.config import Settings, get_settings
from obsidian2anki.core.ai import AI

logger = logging.getLogger(__name__)


class Doctor:
    """Check whether Obsidian2Anki is configured correctly."""

    def run(self) -> None:
        """Run all diagnostic checks."""
        logger.info("Starting application diagnostic checks.")

        environment_checker = EnvironmentChecker(get_settings)
        check_result: Settings | list[AppEnvironmentError] = (
            environment_checker.check_env()
        )

        output_manager = OutputManager()

        if isinstance(check_result, list):
            output_manager.print_table(
                "Environment Results",
                environment_table_columns(),
                check_result,
            )
            logger.warning(
                "Application diagnostic checks failed: "
                "%d environment error(s) detected.",
                len(check_result),
            )
            return

        runtime_checker = RuntimeChecker(
            check_result,
            AnkiManager(),
            AI(),
        )
        runtime_checks = runtime_checker.check_runtime()

        output_manager.print_table(
            "Runtime Results",
            runtime_table_columns(),
            runtime_checks,
        )

        if runtime_checker.passed_checks(runtime_checks):
            logger.info("Application diagnostic checks completed successfully.")
        else:
            failed_checks = sum(not result.passed for result in runtime_checks)
            logger.warning(
                "Application diagnostic checks completed with "
                "%d failed runtime check(s).",
                failed_checks,
            )
