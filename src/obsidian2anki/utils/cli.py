from argparse import ArgumentParser


def build_arg_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="obsidian2anki",
        description="Sync Obsidian notes into Anki flashcards.",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show logging on terminal"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name, help_text in [
        ("migrate", "Run the full migration over the main notes folder."),
        ("process", "Process new notes from the inbox folder."),
        ("clear", "Delete all generated cards and clear state."),
        ("format-notes", "Convert existing notes to the required application format."),
    ]:
        subparsers.add_parser(name, help=help_text)

    delete_card_parser = subparsers.add_parser(
        "delete-card",
        help="Delete a single Anki card by ID.",
    )
    delete_card_parser.add_argument(
        "card_id", help="ID of the Anki card to delete.", type=int
    )

    delete_note_parser = subparsers.add_parser(
        "delete-note",
        help="Delete a note by ID.",
    )
    delete_note_parser.add_argument(
        "note_id", help="ID of the note to delete.", type=str
    )

    return parser
