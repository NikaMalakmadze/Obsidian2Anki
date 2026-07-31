from dataclasses import dataclass


@dataclass
class CheckResult:
    """Result of a single diagnostic check."""

    passed: bool
    message: str
