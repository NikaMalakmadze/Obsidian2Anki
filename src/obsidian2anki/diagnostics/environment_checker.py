from collections.abc import Callable, Mapping
from pydantic_settings import SettingsError
from pydantic_core import ErrorDetails
from pydantic import ValidationError
import logging

from obsidian2anki.diagnostics.models import AppEnvironmentError
from obsidian2anki.config import Settings


logger = logging.getLogger(__name__)


class EnvironmentChecker:
    SENSITIVE_FIELD_PARTS: tuple[str, ...] = ("key", "token", "secret", "password")

    def __init__(self, settings_factory: Callable[[], Settings]):
        self._settings_factory = settings_factory

    def check_env(self) -> Settings | list[AppEnvironmentError]:
        try:
            settings: Settings = self._settings_factory()
            return settings
        except ValidationError as exc:
            errors: list[ErrorDetails] = exc.errors(include_input=True)
            processed_errors = [self._process_error(error) for error in errors]
            self._log_errors(processed_errors)
            return processed_errors
        except SettingsError as exc:
            error = AppEnvironmentError(
                field_name="<settings>",
                error_type="settings_error",
                location=(),
                message=str(exc).title(),
                value="-",
            )
            logger.error("Failed to load environment settings: %s", exc)
            return [error]

    @classmethod
    def _process_error(cls, error: ErrorDetails) -> AppEnvironmentError:
        error_type: str = error.get("type", "unknown")
        location = error.get("loc", ())
        field_name = str(location[0]) if location else "unknown"
        message = str(error.get("msg", "Unknown validation error"))
        value = cls._format_value(field_name, error.get("input"))

        return AppEnvironmentError(field_name, error_type, location, message, value)

    @classmethod
    def _format_value(cls, field_name: str, value: object) -> str:
        lower_filed_name: str = field_name.lower()

        if any(part in lower_filed_name for part in cls.SENSITIVE_FIELD_PARTS):
            return "<redacted>"

        if value is None:
            return "None"

        if isinstance(value, Mapping):
            return "<mapping omitted>"

        rendered = repr(value)
        return rendered if len(rendered) <= 120 else f"{rendered[:117]}..."

    @staticmethod
    def _log_errors(errors: list[AppEnvironmentError]) -> None:
        for error in errors:
            if error.error_type == "missing":
                logger.warning(
                    "Environment field '%s' is missing. Message: '%s'",
                    error.field_name,
                    error.message,
                )

            elif error.error_type == "extra_forbidden":
                logger.warning(
                    "Environment field '%s' is not allowed. Message: '%s'",
                    error.field_name,
                    error.message,
                )

            else:
                logger.warning(
                    "Environment field '%s' has invalid value '%s'. "
                    "Error type: '%s'. Message: '%s'",
                    error.field_name,
                    error.value,
                    error.error_type,
                    error.message,
                )
