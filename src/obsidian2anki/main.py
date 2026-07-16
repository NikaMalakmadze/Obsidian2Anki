from typing import Callable
import logging
import sys

from obsidian2anki.utils.cli import build_arg_parser
from obsidian2anki.utils.logger import setup_logger
from obsidian2anki.app import build_app

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    setup_logger()
    args = build_arg_parser().parse_args(argv)

    app = build_app()
    commands: dict[str, Callable[[], None]] = {
        "migrate": app.migrate,
        "process": app.process,
        "clear": app.clear,
        "delete-card": lambda: app.delete_card(args.card_id),
    }

    try:
        commands[args.command]()
    except KeyboardInterrupt:
        logger.warning("Interrupted by user. Exiting.")
        return 130
    except Exception:
        logger.exception("Unhandled error while running '%s'.", args.command)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
