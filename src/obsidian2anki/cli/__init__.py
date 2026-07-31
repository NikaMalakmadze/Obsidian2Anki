from argparse import ArgumentParser
import argcomplete

from obsidian2anki.cli.commands import APP_COMMANDS, DOCTOR_COMMAND
from obsidian2anki.cli.parser import ArgParser


def build_arg_parser() -> ArgumentParser:
    arg_parser: ArgParser = ArgParser()

    arg_parser.add_command(DOCTOR_COMMAND)

    for command in APP_COMMANDS:
        arg_parser.add_command(command)

    argcomplete.autocomplete(arg_parser.parser)

    return arg_parser.parser
