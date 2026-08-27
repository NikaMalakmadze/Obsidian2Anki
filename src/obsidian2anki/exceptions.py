class O2ABaseException(Exception):
    pass


class ObsidianFolderDoesNotExists(O2ABaseException):
    pass


class AIError(O2ABaseException):
    pass


class AIInvalidOutput(AIError):
    pass


class AIRequestFailed(AIError):
    pass


class AnkiError(O2ABaseException):
    """Base exception for Anki-related failures."""


class AnkiConnectionError(AnkiError):
    """AnkiConnect could not be reached."""


class AnkiResponseError(AnkiError):
    """AnkiConnect returned a malformed response."""


class AnkiActionError(AnkiError):
    """AnkiConnect executed the request but rejected the action."""


class AnkiDuplicateNoteError(AnkiActionError):
    """Anki rejected one or more notes as duplicates."""
