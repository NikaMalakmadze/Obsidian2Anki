from collections.abc import Callable
from argparse import Namespace

from obsidian2anki.cli.handlers import CommandHandler, ArgCommandHandler, ArgTypes
from obsidian2anki.cli.commands import CommandDefinition, APP_COMMANDS
from obsidian2anki.app.app import Obsidian2Anki


def generate_app_command_mapping(
    app: Obsidian2Anki, args: Namespace
) -> dict[str, CommandHandler | ArgCommandHandler]:
    dry_run: bool = getattr(args, "dry_run", False)
    recursive: bool = getattr(args, "recursive", False)

    commands_mapping: dict[str, CommandHandler | ArgCommandHandler] = {}

    for command in APP_COMMANDS:
        method: Callable = getattr(app, command.func_name)
        name: str = command.name

        if isinstance(command, CommandDefinition):
            kwargs: dict[str, bool] = {}

            if command.supports_dry_run:
                kwargs["dry_run"] = dry_run

            if command.supports_recursive:
                kwargs["recursive"] = recursive

            commands_mapping[name] = lambda method=method, kwargs=kwargs: method(
                **kwargs
            )
            continue

        argument: ArgTypes = getattr(args, command.arg_name, None)
        commands_mapping[name] = lambda method=method, argument=argument: method(
            argument
        )

    return commands_mapping
