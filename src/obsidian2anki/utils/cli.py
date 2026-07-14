from argparse import ArgumentParser


def build_arg_parser() -> ArgumentParser:
    parser: ArgumentParser = ArgumentParser(
        prog="obsidian2anki", description="Sync Obsidian notes into Anki flashcards."
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "migrate", help="Run the full migration over the main notes folder."
    )
    subparsers.add_parser("process", help="Process new notes from the inbox folder.")
    subparsers.add_parser("clear", help="Delete all generated cards and clear state.")

    delete_parser = subparsers.add_parser(
        "delete-card", help="Delete a single Anki card by id."
    )
    delete_parser.add_argument("card_id", help="ID of the Anki card to delete.")

    return parser
