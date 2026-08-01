from rich.table import Column


def runtime_table_columns() -> tuple[Column, ...]:
    return (
        Column("", justify="center", width=3, no_wrap=True),
        Column("Check", style="bold cyan", no_wrap=True),
        Column("Result", overflow="fold"),
    )


def environment_table_columns() -> tuple[Column, ...]:
    return (
        Column("Field", style="bold cyan", no_wrap=True),
        Column("Error Type", style="bold red", no_wrap=True),
        Column("Location", style="yellow"),
        Column("Message", ratio=3, overflow="fold"),
        Column("Value", style="magenta", overflow="ellipsis"),
    )
