from importlib.metadata import version
from argparse import ArgumentParser

from obsidian2anki.cli.commands import ArgCommandDefinition, CommandDefinition


class ArgParser:
    def __init__(self) -> None:
        self._parser = ArgumentParser(
            prog="obsidian2anki",
            description="Sync Obsidian notes into Anki flashcards.",
        )
        self._commands_parser = self._parser.add_subparsers(
            dest="command", required=True
        )
        self._init_base_args()

    @property
    def parser(self) -> ArgumentParser:
        return self._parser

    def add_command(self, command: CommandDefinition | ArgCommandDefinition) -> None:
        command_parser = self._commands_parser.add_parser(
            command.name, help=command.help
        )

        if isinstance(command, ArgCommandDefinition):
            command_parser.add_argument(
                command.arg_name, help=command.arg_help, type=command.handler
            )
            return

        if command.supports_dry_run:
            self._add_dry_run(command_parser)

        if command.supports_recursive:
            self._add_recursive(command_parser)

    def _init_base_args(self) -> None:
        self._parser.add_argument(
            "-v", "--verbose", action="store_true", help="Increase output verbosity"
        )
        self._parser.add_argument(
            "--version",
            action="version",
            version=f"%(prog)s {version('obsidian2anki')}",
        )

    @staticmethod
    def _add_dry_run(command_parser: ArgumentParser) -> None:
        command_parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be changed without making any changes.",
        )

    @staticmethod
    def _add_recursive(command_parser: ArgumentParser) -> None:
        command_parser.add_argument(
            "--recursive",
            action="store_true",
            help="Process directories recursively.",
        )
