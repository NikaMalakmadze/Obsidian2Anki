from logging.handlers import RotatingFileHandler
from rich.logging import RichHandler
import logging

from obsidian2anki.config import BASE_DIR

LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "obsidian2anki.log"


def setup_logger(level=logging.INFO, console: bool = True) -> None:
    LOG_DIR.mkdir(exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("google_genai").setLevel(logging.WARNING)

    if root_logger.handlers:
        return

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
    )

    root_logger.addHandler(file_handler)

    if not console:
        return

    console_handler = RichHandler(
        level=level,
        show_time=True,
        show_level=True,
        show_path=False,
        rich_tracebacks=True,
        markup=False,
    )
    console_handler.setFormatter(logging.Formatter("%(message)s"))

    root_logger.addHandler(console_handler)
