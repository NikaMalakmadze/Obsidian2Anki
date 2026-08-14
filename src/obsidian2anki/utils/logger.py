from logging.handlers import RotatingFileHandler
from rich.logging import RichHandler
from argparse import Namespace
import logging

from obsidian2anki.constants import IGNORE_CONSOLE
from obsidian2anki.config import BASE_DIR

LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "obsidian2anki.log"


CONSOLE_HANDLER_NAME = "obsidian2anki_console"
FILE_HANDLER_NAME = "obsidian2anki_file"


def setup_logger(args: Namespace) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    level = (logging.INFO, logging.DEBUG)[args.verbose]
    console_enabled = args.command not in IGNORE_CONSOLE

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    _cofigure_third_party_loggers()
    _configure_file_handler(root_logger, level)
    _configure_console_handler(root_logger, level, console_enabled)


def _cofigure_third_party_loggers() -> None:
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("google_genai").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def _configure_console_handler(
    root_logger: logging.Logger, level: int, enabled: bool
) -> None:
    handler: logging.Handler | None = _find_handler(root_logger, CONSOLE_HANDLER_NAME)

    if not enabled:
        if handler is not None:
            root_logger.removeHandler(handler)
            handler.close()
        return

    if handler is not None:
        handler.setLevel(level)
        return

    handler = RichHandler(
        level=level,
        show_time=True,
        show_level=True,
        show_path=False,
        rich_tracebacks=True,
        markup=False,
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler.name = CONSOLE_HANDLER_NAME

    root_logger.addHandler(handler)


def _configure_file_handler(root_logger: logging.Logger, level: int) -> None:
    handler: logging.Handler | None = _find_handler(root_logger, FILE_HANDLER_NAME)

    if handler is None:
        handler = RotatingFileHandler(
            LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
        )
        handler.name = FILE_HANDLER_NAME
        root_logger.addHandler(handler)

    handler.setLevel(level)


def _find_handler(logger: logging.Logger, name: str) -> logging.Handler | None:
    return next((handler for handler in logger.handlers if handler.name == name), None)
