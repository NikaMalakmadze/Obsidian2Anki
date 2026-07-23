from typing import Callable
import argcomplete
import logging
import sys

from obsidian2anki.cli.parser import build_arg_parser
from obsidian2anki.utils.logger import setup_logger
from obsidian2anki.app import build_app

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    argcomplete.autocomplete(parser)
    args = parser.parse_args(argv)

    setup_logger(
        level=(logging.INFO, logging.DEBUG)[args.verbose],
        console=args.command != "doctor",
    )

    app = build_app()
    commands: dict[str, Callable[[], None]] = {
        "migrate": app.migrate,
        "process": app.process,
        "clear": app.clear,
        "format-notes": app.format_notes,
        "doctor": app.doctor,
        "delete-card": lambda: app.delete_card(args.card_id),
        "delete-note": lambda: app.delete_note(args.note_id),
    }

    try:
        commands[args.command](args.dry_run)
    except KeyboardInterrupt:
        logger.warning("Interrupted by user. Exiting.")
        return 130
    except Exception:
        logger.exception("Unhandled error while running '%s'.", args.command)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
