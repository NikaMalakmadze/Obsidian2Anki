from collections.abc import Sequence
from rich.table import Column, Table
from rich.console import Console
from rich import box

from obsidian2anki.diagnostics.models import TableDataItem


class OutputManager:
    def __init__(self) -> None:
        self._console = Console()

    def print_table(
        self, title: str, columns: Sequence[Column], data: Sequence[TableDataItem]
    ) -> None:
        table = Table(
            *columns,
            title=f"[bold magenta]{title}[/]",
            box=box.ROUNDED,
            highlight=True,
        )

        column_count: int = len(columns)

        for item in data:
            row: tuple[str, ...] = item.render()
            row_len: int = len(row)

            if row_len != column_count:
                raise ValueError(f"Expected {column_count} cells, received {row_len}.")

            table.add_row(*row)

        self._console.print(table)
