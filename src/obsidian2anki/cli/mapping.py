from collections.abc import Callable
from argparse import Namespace

from obsidian2anki.cli.commands import (
    CommandDefinition,
    ArgCommandDefinition,
    APP_COMMANDS,
)
from obsidian2anki.cli.handlers import CommandHandler, ArgCommandHandler, ArgTypes
from obsidian2anki.app.app import Obsidian2Anki


def generate_app_command_mapping(
    app: Obsidian2Anki, args: Namespace
) -> dict[str, CommandHandler | ArgCommandHandler]:
    dry_run: bool = getattr(args, "dry_run", False)
    recursive: bool = getattr(args, "recursive", False)
    force: bool = getattr(args, "force", False)

    commands_mapping: dict[str, CommandHandler | ArgCommandHandler] = {}

    for command in APP_COMMANDS:
        method: Callable = getattr(app, command.func_name)
        name: str = command.name

        kwargs: dict[str, bool] = {}

        if command.supports_force:
            kwargs["force"] = force

        if isinstance(command, CommandDefinition):
            if command.supports_dry_run:
                kwargs["dry_run"] = dry_run

            if command.supports_recursive:
                kwargs["recursive"] = recursive

            commands_mapping[name] = lambda method=method, kwargs=kwargs: method(
                **kwargs
            )
        elif isinstance(command, ArgCommandDefinition):
            argument: ArgTypes = getattr(args, command.arg_name, None)
            commands_mapping[name] = (
                lambda method=method, argument=argument, kwargs=kwargs: method(
                    argument, **kwargs
                )
            )

    return commands_mapping
