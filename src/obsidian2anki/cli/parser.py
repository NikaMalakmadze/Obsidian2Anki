from importlib.metadata import version
from argparse import ArgumentParser

from obsidian2anki.cli.commands import COMMANDS, ARG_COMMANDS


def build_arg_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="obsidian2anki",
        description="Sync Obsidian notes into Anki flashcards.",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Increase output verbosity"
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {version('obsidian2anki')}"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in COMMANDS:
        command_parser = subparsers.add_parser(command.name, help=command.help)
        if command.supports_dry_run:
            command_parser.add_argument(
                "--dry-run",
                action="store_true",
                help="Show what would be changed without making any changes.",
            )

    for arg_command in ARG_COMMANDS:
        arg_command_parser = subparsers.add_parser(
            arg_command.name, help=arg_command.help
        )
        arg_command_parser.add_argument(
            arg_command.arg_name, help=arg_command.arg_help, type=arg_command.handler
        )

    return parser
