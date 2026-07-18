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

    subparsers.add_parser(
        "format-notes",
        help="Convert existing notes to the required application format.",
    )

    delete_card_parser = subparsers.add_parser(
        "delete-card",
        help="Delete a single Anki card by ID.",
    )
    delete_card_parser.add_argument(
        "card_id",
        help="ID of the Anki card to delete.",
    )

    delete_note_parser = subparsers.add_parser(
        "delete-note",
        help="Delete a note by ID.",
    )
    delete_note_parser.add_argument(
        "note_id",
        help="ID of the note to delete.",
    )

    return parser
