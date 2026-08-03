import logging
import sys

from obsidian2anki.cli.mapping import generate_app_command_mapping
from obsidian2anki.utils.logger import setup_logger
from obsidian2anki.diagnostics import build_doctor
from obsidian2anki.cli import build_arg_parser
from obsidian2anki.app import build_app

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    setup_logger(args)

    if args.command == "doctor":
        return build_doctor().run()

    app = build_app()
    commands_mapping = generate_app_command_mapping(app, args)

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
