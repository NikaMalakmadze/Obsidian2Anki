import argcomplete
import logging
import sys

from obsidian2anki.cli.mapping import generate_mapping
from obsidian2anki.cli.parser import build_arg_parser
from obsidian2anki.utils.logger import setup_logger
from obsidian2anki import IGNORE_CONSOLE
from obsidian2anki.app import build_app

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    argcomplete.autocomplete(parser)
    args = parser.parse_args(argv)

    is_verbose: bool = (logging.INFO, logging.DEBUG)[args.verbose]
    is_console: bool = args.command not in IGNORE_CONSOLE

    setup_logger(is_verbose, is_console)

    app = build_app()
    commands_mapping = generate_mapping(app, args)

    try:
        commands_mapping[args.command]()
    except KeyboardInterrupt:
        return logger.warning("Interrupted by user. Exiting.") or 130
    except Exception:
        return (
            logger.exception("Unhandled error while running '%s'.", args.command) or 1
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
