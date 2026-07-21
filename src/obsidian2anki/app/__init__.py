from obsidian2anki.app.dependencies import Dependencies
from obsidian2anki.app.app import Obsidian2Anki


def build_app() -> Obsidian2Anki:
    deps: Dependencies = Dependencies()
    return Obsidian2Anki(
        deps._migration,
        deps._processing,
        deps._clear,
        deps._deleting,
        deps._note_formatting,
    )
