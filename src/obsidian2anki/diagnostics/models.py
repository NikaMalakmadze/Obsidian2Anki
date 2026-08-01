from dataclasses import dataclass
from typing import Protocol


class TableDataItem(Protocol):
    def render(self) -> tuple[str, ...]: ...


@dataclass(frozen=True, slots=True)
class AppRuntimeCheck:
    """Result of a single runtime diagnostic check."""

    check: str
    passed: bool
    message: str

    def render(self) -> tuple[str, ...]:
        status = "✅" if self.passed else "❌"
        return status, self.check, self.message


@dataclass(frozen=True, slots=True)
class AppEnvironmentError:
    """A normalized and safely displayable settings error."""

    field_name: str
    error_type: str
    location: tuple[str | int, ...]
    message: str
    value: str

    def render(self) -> tuple[str, ...]:
        location = " → ".join(map(str, self.location)) or "-"

        return (
            self.field_name,
            self.error_type,
            location,
            self.message,
            self.value,
        )
